from typing import Callable, Optional
from .base import Source
from .caches.duckdb_cache import DuckdbCache
from .sources.snowflake_source import SnowflakeSource
from .sources.mssql_source import MsSqlSource

ALL_CONNECTORS: dict[str, Callable[[tuple], Source]] = {
    "source-snowflake": lambda args: SnowflakeSource(*args),
    "source-mssql": lambda args: MsSqlSource(*args),
}


def get_available_connectors() -> list[str]:
    return ALL_CONNECTORS.keys()


def get_source(
    name: str,
    config: dict[str, str],
    streams: Optional[str | list[str]] = None,
    sync: bool = True,
) -> Source:
    source = ALL_CONNECTORS.get(name)
    if source is None:
        raise Exception("Source unknown")
    return source((config, streams, sync))


def get_default_cache(name: str = "default_cache") -> DuckdbCache:
    return DuckdbCache(name)
