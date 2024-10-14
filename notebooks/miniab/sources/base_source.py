from __future__ import annotations

from typing import Optional, NoReturn
from datetime import datetime

from ..colorize import colorize
from ..base import Cache, Processor, ReadResult
from ..caches.duckdb_cache import DuckdbCache


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
        self.discovered_catalog: list[tuple[str]] = []

        if self.sync:
            with self.get_processor() as processor:
                self.discovered_catalog = processor.discover(self)

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
        return [stream[0] for stream in self.discovered_catalog]

    def read(
        self, cache: Optional[Cache] = None, force_full_refresh: bool = False
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

        return cache.get_result(total_record_cached)

    def _read_to_cache(self, cache: Cache, force_full_refresh: bool):
        with self.get_processor() as processor:
            total_record_cached = 0

            existing_streams: list[str] = []
            if not force_full_refresh:
                existing_streams = [
                    table[0] for table in cache.get_sql_engine().sql("SHOW TABLES;").fetchall()
                ]

            stream_to_be_synced = [
                stream
                for stream in self.selected_streams
                if processor.check_stream_to_be_synced(cache, existing_streams, stream)
            ]

            for stream in stream_to_be_synced:
                total_record_cached += processor.write_stream_to_cache(cache, stream)

            return total_record_cached
