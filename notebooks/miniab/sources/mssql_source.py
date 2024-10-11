from __future__ import annotations

import pyodbc
import pandas as pd

from typing import Optional, NoReturn
from datetime import datetime

from ..colorize import colorize
from ..base import CacheBase, ReadResultBase
from ..read_result import ReadResult
from ..duckdb_cache import DuckdbCache


class MsSqlSource:

    def __init__(
        self, config: dict[str, str], streams: Optional[list[str]], sync: bool
    ) -> NoReturn:
        self.config = config
        self.streams = streams
        self.sync = sync

        if self.sync:
            if streams is None:
                with self._connect() as conn:
                    with conn.cursor() as cursor:
                        show_tables = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_TYPE='BASE TABLE';"
                        rows = cursor.execute(show_tables)
                        self.streams = [row[2] for row in rows]

        self.selected_streams = []

    def select_all_streams(self) -> NoReturn:
        self.selected_streams = self.streams or []

    def select_streams(self, streams: list[str]) -> NoReturn:
        self.selected_streams = streams

    def check(self) -> NoReturn:
        if not self.sync:
            return
        with self._connect() as conn:
            with conn.cursor() as cursor:
                show_tables = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';"
                try:
                    cursor.execute(show_tables)
                except:  # noqa: E722
                    raise Exception("Check failed")

    def read(self, cache: Optional[CacheBase]) -> ReadResultBase:
        if cache is None:
            cache = DuckdbCache()

        time_start = datetime.now()
        print(
            colorize(
                f"Sync Progress: {str(self)} -> {str(cache)}", color="yellow", bold=True
            )
        )

        total_record_num = 0

        if len(self.selected_streams) == 0:
            self.select_all_streams()

        if self.sync:
            with self._connect() as conn:
                print(
                    colorize(
                        f"Started reading from source at {time_start.strftime('%H:%M:%S')}",
                        bold=True,
                    )
                )
                print(f" * Received records for {len(self.streams)} streams:")

                for stream in self.selected_streams:
                    with conn.cursor() as cursor:
                        table_schema = self._generate_table_schema(stream, cursor)
                        cache.processor.sql(table_schema)

                        sql_query = f'SELECT * FROM "{stream}"'
                        cursor.execute(sql_query)

                        record_num = 0
                        for batch in self._get_result_batches(cursor):
                            print(f"  - {record_num:,} {stream} (loading ...)", end="\r")
                            batch_df = self._to_pandas(cursor, batch)
                            cache.processor.sql(f"INSERT INTO {stream} SELECT * FROM batch_df;")
                            record_num += batch_df.shape[0]
                        print(f"  - {record_num:,} {stream}                  ")

                        total_record_num += record_num

            print(f" * Cached {total_record_num:,} records.")

            print(
                f" * Finished reading from source at {datetime.now().strftime('%H:%M:%S')}."
            )

        time_end = datetime.now()
        print(
            colorize(
                f"Sync completed at {time_end.strftime('%H:%M:%S')}. Total time elapsed: {time_end - time_start}",
                bold=True,
            )
        )

        return ReadResult(cache, total_record_num)

    def __str__(self) -> str:
        return "MsSqlSource"

    def _connect(self) -> pyodbc.Connection:
        sql_server_drivers = list(filter(lambda x: "SQL Server" in x, pyodbc.drivers()))
        conn_str = (
            f"DRIVER={{{sql_server_drivers[0]}}};"
            f'SERVER=tcp:{self.config["server"]};PORT=1433;'
            f'DATABASE={self.config["database"]};'
            f'UID={self.config["uid"]};'
            f'PWD={self.config["pwd"]}'
        )
        return pyodbc.connect(conn_str)

    def _get_result_batches(self, data: pyodbc.Cursor, max_chunk_size: int = 100_000):
        while True:
            batch = data.fetchmany(max_chunk_size)
            if not batch:
                break
            yield batch

    def _to_pandas(self, cursor: pyodbc.Cursor, data: list[pyodbc.Row]) -> pd.DataFrame:
        return pd.DataFrame.from_records(
            data,
            columns=[col[0] for col in cursor.description],
        ).map(
            lambda x: str(x) if not isinstance(x, bool) else x,
            na_action="ignore",
        )

    def _generate_table_schema(self, stream: str, data: pyodbc.Cursor) -> str:
        column_names = [
            f'"{column[3]}" {self._to_sql_type(column)}'
            for column in data.columns(table=stream)
        ]
        create_table = f'CREATE OR REPLACE TABLE "{stream}" ('
        create_table += ",".join(column_names)
        create_table += ")"
        return create_table

    def _to_sql_type(self, column: list) -> str:
        types = column[5].split()
        type, _ = (types[0], "") if len(types) == 1 else column[5].split()
        match type:
            case "tinyint":
                return "TINYINT"
            case "smallint":
                return "SMALLINT"
            case "int":
                return "INTEGER"
            case "bigint":
                return "BIGINT"
            case "bit":
                return "BIT"

            case "numeric":
                return f"DECIMAL({column[6]},{column[8]})"
            case "decimal":
                return f"DECIMAL({column[6]},{column[8]})"
            case "money":
                return f"DECIMAL({column[6]},{column[8]})"

            case "float":
                return "FLOAT"
            case "double":
                return "DOUBLE"
            case "real":
                return "REAL"

            case "char":
                return f"VARCHAR({column[6]})"
            case "varchar":
                return f"VARCHAR({column[6]})"
            case "nchar":
                return f"VARCHAR({column[6]})"
            case "nvarchar":
                return f"VARCHAR({column[6]})"
            case "ntext":
                return f"VARCHAR({column[6]})"

            case "date":
                return "DATE"
            case "datetime":
                return "DATE"
            case "datetime2":
                return "DATE"
            case "time":
                return "TIME"
            case "timestamp":
                return "TIMESTAMP"

            case "uniqueidentifier":
                return "UUID"

            case _:
                raise Exception("Invalid or not supported type: " + str(column))
