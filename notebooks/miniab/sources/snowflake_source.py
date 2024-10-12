from __future__ import annotations

import snowflake.connector as sc

from typing import Optional, NoReturn
from datetime import datetime

from ..colorize import colorize
from ..base import Cache, ReadResult
from ..caches.duckdb_cache import DuckdbCache


class SnowflakeSource:

    def __init__(
        self,
        config: dict[str, str],
        streams: Optional[str | list[str]] = None,
        sync: bool = True,
    ) -> NoReturn:
        self.config = config
        self.sync = sync

        self.selected_streams: list[str] = []
        self.discovered_catalog: list[dict | tuple] = []

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
        return [stream[1] for stream in self.discovered_catalog]

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
        return "SnowflakeSource"

    def _connect(self) -> sc.SnowflakeConnection:
        return sc.connect(
            user=self.config["username"],
            password=self.config["password"],
            account=self.config["account"],
            warehouse=self.config["warehouse"],
            database=self.config["database"],
            schema=self.config["schema"],
            role=self.config["role"],
        )

    def _discover(self) -> list[dict | tuple]:
        with self._connect() as conn:
            show_tables = "SHOW TERSE TABLES;"
            cursor = conn.cursor().execute(show_tables)
            assert cursor is not None
            return [row for row in cursor]

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
                sql_query = f"""
                    SELECT
                        *
                    FROM
                        "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
                """
                cursor = conn.cursor().execute(sql_query)
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
                    sql_query = f'INSERT INTO "{stream}" SELECT * FROM batch_df;'
                    cache.processor.sql(sql_query)
                    record_num += batch_df.shape[0]
                print(f"  - {record_num:,} {stream}                  ")

                total_record_cached += record_num

        return total_record_cached

    def _check_if_stream_to_be_cached(
        self, cache: DuckdbCache, conn: sc.SnowflakeConnection, existing_streams: list[str], stream: str
    ):
        to_be_synced = True

        sql_query = f"""
            SELECT
                COUNT(*)
            FROM
                "{self.config["database"]}"."{self.config["schema"]}"."{stream}"
        """
        cursor = conn.cursor().execute(sql_query)
        assert cursor is not None
        (record_num,) = cursor.fetchone()

        if stream in existing_streams:
            sql_query = f'SELECT COUNT(*) FROM "{stream}"'
            (cached_record_num,) = cache.processor.sql(sql_query).fetchone()
            to_be_synced = record_num != cached_record_num

        return to_be_synced

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
