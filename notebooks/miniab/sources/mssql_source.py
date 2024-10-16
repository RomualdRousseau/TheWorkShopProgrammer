from __future__ import annotations

from textwrap import dedent
from typing import Generator, NoReturn, Optional

import pandas as pd
import pyodbc

from ..base import Processor
from .base_source import BaseSource


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
    def __init__(self, config: dict[str, str], max_batch_size=100_000):
        self.config = config
        self.max_batch_size = max_batch_size
        self.conn = pyodbc.connect(
            (
                f"DRIVER={{{self._get_driver()}}};"
                f'SERVER=tcp:{self.config["host"]};PORT={self.config["port"]};'
                f'DATABASE={self.config["database"]};'
                f'UID={self.config["username"]};'
                f'PWD={self.config["password"]}'
            )
        )

    def close(self) -> NoReturn:
        self.conn.close()

    def discover_catalog(self) -> dict[str, tuple]:
        with self.conn.cursor() as cursor:

            def get_tables():
                show_tables = dedent(
                    f"""
                    SELECT
                        *
                    FROM
                        INFORMATION_SCHEMA.TABLES
                    WHERE
                        TABLE_CATALOG='{self.config['database']}'
                        AND TABLE_SCHEMA='{self.config['schema']}'
                        AND TABLE_TYPE='BASE TABLE';
                    """
                )
                return cursor.execute(show_tables).fetchall()

            def get_table_count(stream):
                sql_query = dedent(
                    f"""
                    SELECT
                        COUNT(*)
                    FROM
                        "{self.config["database"]}"."{self.config["schema"]}"."{stream}";
                    """
                )
                return cursor.execute(sql_query).fetchval()

            def zip_table_count(table):
                table_name = table[2]
                return (table_name, get_table_count(table_name))

            return {stream: (count,) for stream, count in map(zip_table_count, get_tables())}

    def generate_table_schema(self, stream: str) -> str:
        with self.conn.cursor() as cursor:
            column_names = [f'"{column[3]}" {self._to_sql_type(column)}' for column in cursor.columns(table=stream)]
            create_table = f'CREATE OR REPLACE TABLE "{stream}" ('
            create_table += ",".join(column_names)
            create_table += ");"
            return create_table

    def get_result_batches(self, stream: str) -> Generator[pd.DataFrame]:
        with self.conn.cursor() as cursor:
            sql_query = dedent(
                f"""
                SELECT
                    *
                FROM
                    "{self.config["database"]}"."{self.config["schema"]}"."{stream}";
                """
            )
            cursor = cursor.execute(sql_query)

            while True:
                batch = cursor.fetchmany(self.max_batch_size)
                if not batch:
                    break
                yield self._to_pandas(cursor, batch)

    def _get_driver(self) -> str:
        return next(filter(lambda x: "SQL Server" in x, pyodbc.drivers()))

    def _to_pandas(self, cursor: pyodbc.Cursor, data: list[pyodbc.Row]) -> pd.DataFrame:
        return pd.DataFrame.from_records(
            data,
            columns=[col[0] for col in cursor.description],
        ).map(
            lambda x: str(x) if not isinstance(x, bool) else x,
            na_action="ignore",
        )

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

            case "float":
                return "FLOAT"
            case "double":
                return "DOUBLE"
            case "real":
                return "REAL"

            case "numeric":
                return f"DECIMAL({column[6]},{column[8]})"
            case "decimal":
                return f"DECIMAL({column[6]},{column[8]})"
            case "money":
                return f"DECIMAL({column[6]},{column[8]})"

            case "char":
                return f"VARCHAR({column[6]})"
            case "varchar":
                return f"VARCHAR({column[6]})"
            case "text":
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
