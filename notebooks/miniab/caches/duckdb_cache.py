from __future__ import annotations

import os
from typing import NoReturn

import pandas as pd
import pyarrow as pa
from sqlalchemy import Engine, create_engine, text

from ..base import Cache, ReadResult


class DuckdbCache:
    def __init__(self, name: str = "default_cache"):
        path = f".cache/{name}"
        if not os.path.exists(path):
            os.makedirs(path)
        self._sql_engine = create_engine(f"duckdb:///{path}/{name}.duckdb")

    def get_sql_engine(self) -> Engine:
        return self._sql_engine

    def get_read_result(self, total_record_cached: int) -> ReadResult:
        return DuckdbReadResult(self, total_record_cached)

    def get_arrow_dataset(self, stream_name: str, max_chunk_size: int = 100_000) -> pa.Table:
        with self._sql_engine.connect() as conn:
            arrow_chunks = []
            sql_query = text(f"SELECT * FROM \"{stream_name}\"")
            for chunk in pd.read_sql_query(sql_query, conn, chunksize=max_chunk_size):
                arrow_chunk = pa.Table.from_pandas(chunk)
                arrow_chunks.append(arrow_chunk)
            return pa.concat_tables(arrow_chunks)

    def execute_sql(self, stmt: str) -> NoReturn:
        with self._sql_engine.connect() as conn:
            conn.execute(text(stmt)).close()

    def do_checkpoint(self) -> NoReturn:
        self.execute_sql("CHECKPOINT;")

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

    def get_sql_engine(self) -> Engine:
        return self._cache.get_sql_engine()

    def to_arrow(self, stream_name: str, max_chunk_size: int = 100_000) -> pa.Table:
        return self._cache.get_arrow_dataset(stream_name, max_chunk_size)
