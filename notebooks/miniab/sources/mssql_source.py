from __future__ import annotations

import pyodbc
import pandas as pd

from typing import Optional, NoReturn
from datetime import datetime

from ..colorize import colorize
from ..base import Cache, ReadResult
from ..caches.duckdb_cache import DuckdbCache


class MsSqlSource:

    def __init__(
        self,
        config: dict[str, str],
        streams: Optional[str | list[str]] = None,
        sync: bool = True,
    ) -> NoReturn:
        self.config = config
        self.sync = sync

        self.selected_streams: list[str] = []
        self.discovered_catalog: list[pyodbc.Row] = []

        if self.sync:
            self.discovered_catalog = self._discover(self)

        if streams is not None:
            self.select_streams(streams)

    def select_all_streams(self) -> NoReturn:
        self.selected_streams = self.get_available_streams()

    def select_streams(self, streams: str | list[str]) -> NoReturn:
        if streams == "*":
            self.select_all_streams()
            return

        if isinstance(streams, str):
            # If a single stream is provided, convert it to a one-item list
            streams = [streams]

        available_streams = self.get_available_streams()
        for stream in streams:
            if stream not in available_streams:
                raise Exception(f"Stream not found: {stream}")
        self.selected_streams = streams

    def get_selected_streams(self) -> list[str]:
        return self.selected_streams

    def get_available_streams(self) -> list[str]:
        return [stream[2] for stream in self.discovered_catalog]

    def read(
        self, cache: Optional[Cache], force_full_refresh: bool = False
    ) -> ReadResult:
        cache = cache or DuckdbCache()

        total_record_cached = 0

        if self.sync:
            if not self.selected_streams:
                raise Exception("No streams selected")

            time_start = datetime.now()
            print(
                colorize(
                    f"Sync Progress: {str(self)} -> {str(cache)}",
                    color="yellow",
                    bold=True,
                )
            )
            print(
                colorize(
                    f"Started reading from source at {time_start.strftime('%H:%M:%S')}",
                    bold=True,
                )
            )

            print(f" * Received records for {len(self.streams)} streams:")
            total_record_cached = self._read_to_cache(cache, force_full_refresh)
            print(f" * Cached {total_record_cached:,} records.")

            time_end = datetime.now()
            print(
                f" * Finished reading from source at {time_end.strftime('%H:%M:%S')}."
            )
            print(
                colorize(
                    f"Sync completed at {time_end.strftime('%H:%M:%S')}. Total time elapsed: {time_end - time_start}",
                    bold=True,
                )
            )

        return cache.get_result(cache, total_record_cached)

    def __str__(self) -> str:
        return "MsSqlSource"

    def _connect(self) -> pyodbc.Connection:
        sql_server_drivers = list(filter(lambda x: "SQL Server" in x, pyodbc.drivers()))
        conn_str = (
            f"DRIVER={{{sql_server_drivers[0]}}};"
            f'SERVER=tcp:{self.config["host"]};PORT={self.config["port"]};'
            f'DATABASE={self.config["database"]};'
            f'UID={self.config["username"]};'
            f'PWD={self.config["password"]}'
        )
        return pyodbc.connect(conn_str)

    def _discover(self) -> list[pyodbc.Row]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                show_tables = f"""
                    SELECT
                        *
                    FROM
                        INFORMATION_SCHEMA.TABLES
                    WHERE
                        TABLE_SCHEMA='{self.config['schema']}' AND TABLE_TYPE='BASE TABLE';
                """
                return cursor.execute(show_tables).fetchall()

    def _read_to_cache(self, cache: DuckdbCache, force_full_refresh: bool):
        total_record_cached = 0

        with self._connect() as conn:

            existing_streams: list[str] = []
            if not force_full_refresh:
                existing_streams = [
                    table[0] for table in cache.processor.sql("SHOW TABLES;").fetchall()
                ]

            def check_if_stream_to_be_cached(stream: str):
                return self._check_if_stream_to_be_cached(
                    cache, conn, existing_streams, stream
                )
            stream_to_be_cached = list(filter(check_if_stream_to_be_cached, self.selected_streams))

            for stream in stream_to_be_cached:
                with conn.cursor() as cursor:
                    table_schema = self._generate_table_schema(stream, cursor)
                    cache.processor.sql(table_schema)

                    sql_query = f"""
                        SELECT
                            *
                        FROM
                            "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
                    """
                    cursor.execute(sql_query)

                    record_num = 0
                    for batch in self._get_result_batches(cursor):
                        print(
                            f"  - {record_num:,} {stream} (loading)",
                            end="\r",
                        )
                        batch_df = self._to_pandas(cursor, batch)
                        sql_query = f'INSERT INTO "{stream}" SELECT * FROM batch_df;'
                        cache.processor.sql(sql_query)
                        record_num += batch_df.shape[0]
                    print(f"  - {record_num:,} {stream}                  ")

                    total_record_cached += record_num

        return total_record_cached

    def _check_if_stream_to_be_cached(
        self,
        cache: DuckdbCache,
        conn: pyodbc.Connection,
        existing_streams: list[str],
        stream: str,
    ):
        to_be_synced = True

        with conn.cursor() as cursor:
            sql_query = f"""
                SELECT
                    COUNT(*)
                FROM
                    "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
            """
            record_num = cursor.execute(sql_query).fetchval()

        if stream in existing_streams:
            sql_query = f'SELECT COUNT(*) FROM "{stream}"'
            (cached_record_num,) = cache.processor.sql(sql_query).fetchone()
            to_be_synced = record_num != cached_record_num

        return to_be_synced

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

    def _generate_table_schema(self, stream: str, cursor: pyodbc.Cursor) -> str:
        column_names = [
            f'"{column[3]}" {self._to_sql_type(column)}'
            for column in cursor.columns(table=stream)
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
