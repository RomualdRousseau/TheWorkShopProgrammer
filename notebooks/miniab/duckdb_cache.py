from __future__ import annotations
from typing import Any

import os
import duckdb
import pyarrow


class DuckdbCache:

    def __init__(self):
        if not os.path.exists(".cache"):
            os.mkdir(".cache")
        self._processor = duckdb.connect(".cache/cache.duckdb")

    @property
    def processor(self) -> Any:
        return self._processor

    def get_arrow_dataset(
        self, stream_name: str, max_chunk_size: int = 100000
    ) -> pyarrow.lib.Table:
        query = self.processor.sql(f"SELECT * FROM {stream_name}")
        return query.to_arrow_table(max_chunk_size)

    def __str__(self) -> str:
        return "DuckdbCache"
