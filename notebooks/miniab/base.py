from typing import Protocol, Any, NoReturn

import duckdb
import pyarrow


class CacheBase(Protocol):

    @property
    def processor(self) -> Any: ...

    def get_arrow_dataset(
        self, stream_name: str, max_chunk_size: int = 100000
    ) -> pyarrow.lib.Table: ...


class ReadResultBase(Protocol):

    @property
    def processed_records(self) -> int: ...

    @property
    def cache(self) -> CacheBase: ...

    def get_sql_engine(self) -> duckdb.DuckDBPyConnection: ...

    def to_arrow(
        self, stream_name: str, max_chunk_size: int = 100000
    ) -> pyarrow.lib.Table: ...


class SourceBase(Protocol):

    def select_all_streams(self) -> NoReturn: ...

    def select_streams(self, streams: list[str]) -> NoReturn: ...

    def get_available_streams(self) -> list[str]: ...

    def check(self) -> NoReturn: ...

    def read(self) -> ReadResultBase: ...
