from __future__ import annotations
from textwrap import dedent

import snowflake.connector as sc

from typing import Generator, Optional, NoReturn

from ..base import Processor
from ..sources.base_source import BaseSource
from ..caches.duckdb_cache import DuckdbCache


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

    def __enter__(self) -> Processor:
        return self

    def __exit__(self, type, value, traceback) -> NoReturn:
        self.close()

    def close(self) -> NoReturn:
        self.conn.close()

    def discover_catalog(self) -> dict[str, tuple]:
        catalog = {}

        show_tables = "SHOW TERSE TABLES;"
        rows = self.conn.cursor().execute(show_tables)
        assert rows is not None

        for row in rows:
            stream = row[1]

            sql_query = dedent(
                f"""
                SELECT
                    COUNT(*)
                FROM
                    "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
                """
            )
            cursor = self.conn.cursor().execute(sql_query)
            assert cursor is not None
            (record_num,) = cursor.fetchone()
            
            catalog[stream] = (record_num,)

        return catalog

    def write_stream_to_cache(
        self, cache: DuckdbCache, stream: str
    ) -> Generator[int, None, None]:
        sql_query = dedent(
            f"""
            SELECT
                *
            FROM
                "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
            """
        )
        cursor = self.conn.cursor().execute(sql_query)
        assert cursor is not None

        table_schema = self._generate_table_schema(stream, cursor)
        cache.processor.sql(table_schema)

        record_num = 0
        for batch in cursor.get_result_batches():
            batch_df = batch.to_pandas()
            sql_query = dedent(
                f"""
                INSERT INTO "{stream}"
                SELECT
                    *
                FROM
                    batch_df;
                """
            )
            cache.processor.sql(sql_query)
            record_num += batch_df.shape[0]
            yield record_num

    def _generate_table_schema(self, stream: str, cursor: sc.SnowflakeCursor) -> str:
        column_names = [
            f"{column.name} {self._to_sql_type(column)}"
            for column in cursor.description
        ]
        create_table = f"CREATE OR REPLACE TABLE {stream} ("
        create_table += ",".join(column_names)
        create_table += ")"
        return create_table

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
                raise Exception("Invalid or not supported type")
