from __future__ import annotations

from textwrap import dedent
from typing import Generator, NoReturn, Optional

import pandas as pd
import snowflake.connector as sc

from ..base import Processor
from .base_source import BaseSource


class SnowflakeSource(BaseSource):
    def __init__(
        self,
        config: dict[str, str],
        streams: Optional[str | list[str]] = None,
        sync: bool = True,
    ) -> NoReturn:
        super().__init__(config, streams, sync)

    def get_processor(self) -> Processor:
        return SnowflakeProcessor(self.config)

    def __str__(self) -> str:
        return "SnowflakeSource"


class SnowflakeProcessor:
    def __init__(self, config: dict[str, str]):
        self.config = config
        self.conn = sc.connect(
            user=self.config["username"],
            password=self.config["password"],
            account=self.config["account"],
            warehouse=self.config["warehouse"],
            database=self.config["database"],
            schema=self.config["schema"],
            role=self.config["role"],
        )

    def close(self) -> NoReturn:
        self.conn.close()

    def discover_catalog(self) -> dict[str, tuple]:
        def get_tables():
            show_tables = dedent(
                """
                SHOW TERSE TABLES;
                """
            )
            cursor = self.conn.cursor().execute(show_tables)
            assert cursor is not None
            return cursor.fetchall()

        def get_table_count(stream):
            sql_query = dedent(
                f"""
                SELECT
                    COUNT(*)
                FROM
                    "{self.config["database"]}"."{self.config["schema"]}"."{stream}";
                """
            )
            cursor = self.conn.cursor().execute(sql_query)
            assert cursor is not None
            return cursor.fetchone()[0]

        def zip_table_count(table):
            table_name = table[1]
            return (table_name, get_table_count(table_name))

        return {stream: (count,) for stream, count in map(zip_table_count, get_tables())}

    def generate_table_schema(self, stream: str) -> str:
        sql_query = dedent(
            f"""
            SELECT TOP(1)
                *
            FROM
                "{self.config["database"]}"."{self.config["schema"]}"."{stream}";
            """
        )
        cursor = self.conn.cursor().execute(sql_query)
        assert cursor is not None

        column_names = [f"{column.name} {self._to_sql_type(column)}" for column in cursor.description]
        create_table = f'CREATE OR REPLACE TABLE "{stream}" ('
        create_table += ",".join(column_names)
        create_table += ");"
        return create_table

    def get_result_batches(self, stream: str) -> Generator[pd.DataFrame]:
        sql_query = dedent(
            f"""
            SELECT
                *
            FROM
                "{self.config["database"]}"."{self.config["schema"]}"."{stream}";
            """
        )
        cursor = self.conn.cursor().execute(sql_query)
        assert cursor is not None

        for batch in cursor.get_result_batches():
            yield batch.to_pandas()

    def _to_sql_type(self, column: sc.ResultMetadata) -> str:
        match column.type_code:
            case 0:
                if column.scale == 0:
                    return "INTEGER"
                else:
                    return f"DECIMAL({column.precision},{column.scale})"
            case 1:
                return "REAL"
            case 2:
                return f"VARCHAR({column.internal_size})"
            case 3:
                return "DATE"
            case 4:
                return "TIMESTAMP"
            case _:
                raise Exception("Invalid or not supported type: " + str(column))
