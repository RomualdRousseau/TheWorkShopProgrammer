from __future__ import annotations

import duckdb
import pyarrow

from .base import CacheBase


class ReadResult:

    def __init__(self, cache: CacheBase, processed_records: int):
        self._cache = cache
        self._processed_records = processed_records

    @property
    def processed_records(self) -> int:
        return self._processed_records

    @property
    def cache(self) -> CacheBase:
        return self._cache

    def get_sql_engine(self) -> duckdb.DuckDBPyConnection:
        return self._cache.processor

    def to_arrow(self, stream_name: str, max_chunk_size: int = 100000) -> pyarrow.lib.Table:
        return self._cache.get_arrow_dataset(stream_name, max_chunk_size)
