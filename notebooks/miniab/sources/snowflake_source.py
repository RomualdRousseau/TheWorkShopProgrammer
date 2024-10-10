from __future__ import annotations

import snowflake.connector as sc

from typing import Optional, NoReturn
from datetime import datetime

from ..colorize import colorize
from ..base import CacheBase, ReadResultBase
from ..read_result import ReadResult
from ..duckdb_cache import DuckdbCache


class SnowflakeSource:

    def __init__(
        self, config: dict[str, str], streams: Optional[list[str]], sync: bool
    ) -> NoReturn:
        self.config = config
        self.streams = streams
        self.sync = sync

        if self.sync:
            with self._connect() as conn:
                if streams is None:
                    show_tables = "SHOW TERSE TABLES;"
                    tables = conn.cursor().execute(show_tables)
                    self.streams = [table[1] for table in tables]

        self.selected_streams = []

    def select_all_streams(self) -> NoReturn:
        self.selected_streams = self.streams or []

    def select_streams(self, streams: list[str]) -> NoReturn:
        self.selected_streams = streams

    def check(self) -> NoReturn:
        if not self.sync:
            return
        with self._connect() as conn:
            show_tables = "SHOW TERSE TABLES;"
            data = conn.cursor().execute(show_tables)
            if data is None:
                raise Exception("Check failed")

    def read(self, cache: Optional[CacheBase]) -> ReadResultBase:
        if cache is None:
            cache = DuckdbCache()

        time_start = datetime.now()
        print(colorize(f"Sync Progress: {str(self)} -> {str(cache)}", color="yellow", bold=True))

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
                    sql_query = f'SELECT * FROM "{self.config["database"]}"."{self.config["schema"]}"."{stream}"'
                    data = conn.cursor().execute(sql_query)

                    table_schema = self._generate_table_schema(stream, data)
                    cache.processor.sql(table_schema)

                    record_num = 0
                    for batch in data.get_result_batches():
                        batch_df = batch.to_pandas()  # noqa: F841
                        cache.processor.sql(f"INSERT INTO {stream} SELECT * FROM batch_df;")
                        record_num += batch_df.shape[0]
                    print(f"  - {record_num} {stream}")

                    total_record_num += record_num

            print(f" * Cached {total_record_num} records.")

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

    def _generate_table_schema(self, stream: str, data: sc.SnowflakeCursor) -> str:
        column_names = [
            f"{column.name} {self._to_sql_type(column)}" for column in data.description
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
