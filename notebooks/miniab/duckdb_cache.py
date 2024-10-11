from __future__ import annotations
from typing import Any

import os
import duckdb
import pyarrow


class DuckdbCache:

    def __init__(self, name: str):
        path = f".cache/{name}"
        if not os.path.exists(path):
            os.makedirs(path)
        self._processor = duckdb.connect(f"{path}/{name}.duckdb")

    @property
    def processor(self) -> Any:
        return self._processor

    def get_arrow_dataset(
        self, stream_name: str, max_chunk_size: int = 100_000
    ) -> pyarrow.lib.Table:
        sql_query = self._processor.sql(f"SELECT * FROM \"{stream_name}\"")
        return sql_query.to_arrow_table(max_chunk_size)

    def __str__(self) -> str:
        return "DuckdbCache"
