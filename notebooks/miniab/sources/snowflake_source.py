from __future__ import annotations
from textwrap import dedent

import snowflake.connector as sc

from typing import Optional, NoReturn, override

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

    @override
    def get_processor(self) -> Processor:
        return SnowflakeProcessor(self.config)

    def __str__(self) -> str:
        return "SnowflakeSource"


class SnowflakeProcessor:

    def __init__(self, config: dict[str, str]):
        self.conn = sc.connect(
            user=config["username"],
            password=config["password"],
            account=config["account"],
            warehouse=config["warehouse"],
            database=config["database"],
            schema=config["schema"],
            role=config["role"],
        )

    def close(self) -> NoReturn:
        self.conn.close()

    def discover(self) -> list[tuple[str]]:
        show_tables = "SHOW TERSE TABLES;"
        cursor = self.conn.cursor().execute(show_tables)
        assert cursor is not None
        return [(row[1]) for row in cursor]

    def check_stream_to_be_synced(
        self, cache: DuckdbCache, existing_streams: list[str], stream: str
    ) -> bool:
        to_be_synced = True

        sql_query = dedent(
            f"""
            SELECT
                COUNT(*)
            FROM
                "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
            """)
        cursor = self.conn.cursor().execute(sql_query)
        assert cursor is not None
        (record_num,) = cursor.fetchone()

        if stream in existing_streams:
            sql_query = f'SELECT COUNT(*) FROM "{stream}"'
            (cached_record_num,) = cache.processor.sql(sql_query).fetchone()
            to_be_synced = record_num != cached_record_num

        return to_be_synced

    def write_stream_to_cache(self, cache: DuckdbCache, stream: str) -> int:
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
            print(
                f"  - {record_num:,} {stream} (loading)",
                end="\r",
            )
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
        print(f"  - {record_num:,} {stream}                  ")

        return record_num

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
