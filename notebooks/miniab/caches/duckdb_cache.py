from __future__ import annotations

import os
import duckdb
import pyarrow

from ..base import Cache, ReadResult


class DuckdbCache:

    def __init__(self, name: str):
        path = f".cache/{name}"
        if not os.path.exists(path):
            os.makedirs(path)
        self._processor = duckdb.connect(f"{path}/{name}.duckdb")

    @property
    def processor(self) -> duckdb.DuckDBPyConnection:
        return self._processor

    def get_result(self, total_record_cached: int) -> ReadResult:
        return DuckdbReadResult(self, total_record_cached)

    def get_arrow_dataset(
        self, stream_name: str, max_chunk_size: int = 100_000
    ) -> pyarrow.lib.Table:
        sql_query = self._processor.sql(f'SELECT * FROM "{stream_name}"')
        return sql_query.to_arrow_table(max_chunk_size)

    def __str__(self) -> str:
        return "DuckdbCache"


class DuckdbReadResult:

    def __init__(self, cache: Cache, processed_records: int):
        self._cache = cache
        self._processed_records = processed_records

    @property
    def processed_records(self) -> int:
        return self._processed_records

    @property
    def cache(self) -> Cache:
        return self._cache

    def get_sql_engine(self) -> duckdb.DuckDBPyConnection:
        return self._cache.processor

    def to_arrow(
        self, stream_name: str, max_chunk_size: int = 100000
    ) -> pyarrow.lib.Table:
        return self._cache.get_arrow_dataset(stream_name, max_chunk_size)
