from __future__ import annotations

import os
from typing import NoReturn

import duckdb
import pyarrow

from notebooks.miniab.base import Cache, ReadResult


class DuckdbCache:
    def __init__(self, name: str = "default_cache"):
        path = f".cache/{name}"
        if not os.path.exists(path):
            os.makedirs(path)
        self._sql_engine = duckdb.connect(f"{path}/{name}.duckdb")

    def get_sql_engine(self) -> duckdb.DuckDBPyConnection:
        return self._sql_engine

    def execute_sql(self, stmt: str) -> NoReturn:
        self._sql_engine.sql(stmt)

    def fetchone_sql(self, stmt: str) -> tuple | None:
        return self._sql_engine.sql(stmt).fetchone()

    def fetchall_sql(self, stmt: str) -> list[tuple]:
        return self._sql_engine.sql(stmt).fetchall()

    def get_read_result(self, total_record_cached: int) -> ReadResult:
        return DuckdbReadResult(self, total_record_cached)

    def get_arrow_dataset(self, stream_name: str, max_chunk_size: int = 100_000) -> pyarrow.lib.Table:
        sql_query = self._sql_engine.sql(f'SELECT * FROM "{stream_name}"')
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
        return self._cache.get_sql_engine()

    def to_arrow(self, stream_name: str, max_chunk_size: int = 100000) -> pyarrow.lib.Table:
        return self._cache.get_arrow_dataset(stream_name, max_chunk_size)
