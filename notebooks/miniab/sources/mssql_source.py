from __future__ import annotations
from textwrap import dedent

import pyodbc
import pandas as pd

from typing import Generator, Optional, NoReturn

from .base_source import BaseSource
from ..base import Processor
from ..caches.duckdb_cache import DuckdbCache


class MsSqlSource(BaseSource):

    def __init__(
        self,
        config: dict[str, str],
        streams: Optional[str | list[str]] = None,
        sync: bool = True,
    ) -> NoReturn:
        super().__init__(config, streams, sync)

    def get_processor(self) -> Processor:
        return MsSqlProcessor(self.config)

    def __str__(self) -> str:
        return "MsSqlSource"


class MsSqlProcessor:

    def __init__(self, config: dict[str, str]):
        self.config = config
        self.conn = pyodbc.connect(
            (
                f"DRIVER={{{self._get_driver()}}};"
                f'SERVER=tcp:{self.config["host"]};PORT={self.config["port"]};'
                f'DATABASE={self.config["database"]};'
                f'UID={self.config["username"]};'
                f'PWD={self.config["password"]}'
            )
        )

    def __enter__(self) -> Processor:
        return self

    def __exit__(self, type, value, traceback) -> NoReturn:
        self.close()

    def close(self) -> NoReturn:
        self.conn.close()

    def discover_catalog(self) -> dict[str, tuple]:
        catalog = {}

        with self.conn.cursor() as cursor:
            show_tables = dedent(
                f"""
                SELECT
                    *
                FROM
                    INFORMATION_SCHEMA.TABLES
                WHERE
                    TABLE_CATALOG='{self.config['database']}' AND TABLE_SCHEMA='{self.config['schema']}' AND TABLE_TYPE='BASE TABLE';
                """
            )
            rows = cursor.execute(show_tables).fetchall()

            for row in rows:
                stream = row[2]

                sql_query = dedent(
                    f"""
                    SELECT
                        COUNT(*)
                    FROM
                        "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
                    """
                )
                record_num = cursor.execute(sql_query).fetchval()

                catalog[stream] = (record_num,)

        return catalog

    def write_stream_to_cache(
        self, cache: DuckdbCache, stream: str
    ) -> Generator[int, None, None]:
        with self.conn.cursor() as cursor:
            table_schema = self._generate_table_schema(stream, cursor)
            cache.get_sql_engine().sql(table_schema)

            sql_query = dedent(
                f"""
                SELECT
                    *
                FROM
                    "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
                """
            )
            cursor.execute(sql_query)

            record_num = 0
            for batch in self._get_result_batches(cursor):
                batch_df = self._to_pandas(cursor, batch)
                sql_query = dedent(
                    f"""
                    INSERT INTO "{stream}"
                    SELECT
                        *
                    FROM
                        batch_df;
                    """
                )
                cache.get_sql_engine().sql(sql_query)
                record_num += batch_df.shape[0]
                yield record_num

    def _get_driver(self) -> str:
        return next(filter(lambda x: "SQL Server" in x, pyodbc.drivers()))

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
