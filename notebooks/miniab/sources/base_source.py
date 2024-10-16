from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from textwrap import dedent
from typing import Generator, NoReturn, Optional

from sqlalchemy import Engine, MetaData, Table, inspect, text

from ..base import Cache, Processor, ReadResult
from ..caches import get_default_cache
from ..colorize import colorize


class BaseSource:
    def __init__(
        self,
        config: dict[str, str],
        streams: Optional[str | list[str]] = None,
        sync: bool = True,
    ) -> NoReturn:
        self.config = config
        self.sync = sync

        self.selected_streams: list[str] = []
        self.discovered_catalog: dict[str, tuple] = {}

        if self.sync:
            with self._autoclose_processor() as processor:
                self.discovered_catalog = processor.discover_catalog()

        if streams is not None:
            self.select_streams(streams)

    def get_processor(self) -> Processor:
        raise Exception("not implemented")

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
        return list(self.discovered_catalog.keys())

    def read(
        self, cache: Optional[Cache] = None, force_full_refresh: bool = False
    ) -> ReadResult:
        cache = cache or get_default_cache()

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

            engine = cache.get_sql_engine()
            existing_streams = inspect(engine).get_table_names()
            stream_to_be_synced = [
                stream
                for stream in self.selected_streams
                if force_full_refresh
                or stream not in existing_streams
                or self._check_stream_to_be_synced(engine, stream)
            ]

            if len(stream_to_be_synced) > 0:
                print(f" * Received records for {len(stream_to_be_synced)} streams:")
                total_record_cached = self._read_to_cache(engine, stream_to_be_synced, existing_streams)
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

        cache.do_checkpoint()

        return cache.get_read_result(total_record_cached)

    def _check_stream_to_be_synced(self, engine: Engine, stream: str) -> bool:
        def get_cached_count():
            sql_query = dedent(
                f"""
                SELECT
                    COUNT(*)
                FROM
                    "{stream}";
                """
            )
            with engine.connect() as conn:
                return conn.execute(text(sql_query)).scalar()

        def compare_with_catalog(cached_count):
            discovered_count = self.discovered_catalog[stream][0]
            return discovered_count - cached_count

        return compare_with_catalog(get_cached_count()) != 0

    def _read_to_cache(self, engine: Engine, streams: list[str], existing_streams: list[str]) -> int:
        with self._autoclose_processor() as processor:

            def write_stream_to_new_table(stream, total_record_count):
                record_count = 0

                progress = record_count / total_record_count
                print(f"  - {record_count:,} {stream} ({progress:.0%})", end="\r")

                if stream in existing_streams:
                    Table(stream, MetaData()).drop(engine)

                for batch in processor.get_result_batches(stream):
                    batch.to_sql(
                        stream, engine, if_exists="append", index=False
                    )
                    record_count += batch.shape[0]
                    progress = record_count / total_record_count
                    print(f"  - {record_count:,} {stream} ({progress:.0%})", end="\r")

                assert record_count == total_record_count
                print(f"  - {record_count:,} {stream} {' '*10}")
                return record_count

            total_record_cached = 0
            for stream in streams:
                total_record_count = self.discovered_catalog[stream][0]
                total_record_cached += (
                    write_stream_to_new_table(stream, total_record_count)
                    if total_record_count > 0
                    else 0
                )

            return total_record_cached

    @contextmanager
    def _autoclose_processor(self) -> Generator[Processor]:
        processor = self.get_processor()
        yield processor
        processor.close()
