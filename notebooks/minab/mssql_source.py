from __future__ import annotations

import pytds

from typing import Optional, NoReturn
from datetime import datetime

from .colorize import colorize
from .base import CacheBase, ReadResultBase
from .read_result import ReadResult
from .duckdb_cache import DuckdbCache


class MsSqlSource:

    def __init__(
        self, config: dict[str, str], streams: Optional[list[str]], sync: bool
    ) -> NoReturn:
        self.config = config
        self.streams = streams
        self.sync = sync

        if self.sync:
            with self._connect() as conn:
                if streams is None:
                    show_tables = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';"
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
            show_tables = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';"
            data = conn.cursor().execute(show_tables)
            if data is None:
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
                        sql_query = f'SELECT * FROM "{stream}"'
                        data = cursor.execute(sql_query)

                        table_schema = self._generate_table_schema(stream, data)
                        cache.processor.sql(table_schema)

                        record_num = 0
                        for batch in data.get_result_batches():
                            batch_df = batch.to_pandas()  # noqa: F841
                            cache.processor.sql(
                                f"INSERT INTO {stream} SELECT * FROM batch_df;"
                            )
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

    def _connect(self) -> pytds.Connection:
        return pytds.connect(
            dsn=self.config["server"],
            database=self.config["database"],
            user=self.config["uid"],
            password=self.config["pwd"],
        )

    def _generate_table_schema(self, stream: str, data: pytds.Cursor) -> str:
        column_names = [
            f"{column[0]} {self._to_sql_type(column)}" for column in data.description
        ]
        create_table = f"CREATE OR REPLACE TABLE {stream} ("
        create_table += ",".join(column_names)
        create_table += ")"
        return create_table

    def _to_sql_type(self, column: list) -> str:
        print(column)
        match column[1]:
            case pytds.INTEGER:
                return "INTEGER"
            case pytds.DECIMAL:
                return f"DECIMAL({column[4]},{column[5]})"
            case pytds.REAL:
                return "REAL"
            case pytds.STRING:
                return f"VARCHAR({column[2]})"
            case pytds.DATETIME:
                return "DATE"
            case _:
                raise Exception("Invalid or not supported type")
