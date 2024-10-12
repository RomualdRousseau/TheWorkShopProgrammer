from __future__ import annotations
from typing import Optional, Protocol, NoReturn, Any

import pyarrow


class Source(Protocol):

    def select_all_streams(self) -> NoReturn: ...

    def select_streams(self, streams: list[str]) -> NoReturn: ...

    def get_selected_streams(self) -> list[str]: ...

    def get_available_streams(self) -> list[str]: ...

    def read(
        self, cache: Optional[Cache], force_full_refresh: bool = False
    ) -> ReadResult: ...


class Cache(Protocol):

    @property
    def processor(self) -> Any: ...

    def get_result(self, total_record_cached: int) -> ReadResult: ...

    def get_arrow_dataset(
        self, stream_name: str, max_chunk_size: int = 100000
    ) -> pyarrow.lib.Table: ...


class ReadResult(Protocol):

    @property
    def processed_records(self) -> int: ...

    @property
    def cache(self) -> Cache: ...

    def get_sql_engine(self) -> Any: ...

    def to_arrow(
        self, stream_name: str, max_chunk_size: int = 100000
    ) -> pyarrow.lib.Table: ...
