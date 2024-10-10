from typing import Optional

from .base import SourceBase
from .duckdb_cache import DuckdbCache
from .sources.snowflake_source import SnowflakeSource
from .sources.mssql_source import MsSqlSource


def get_source(
    name: str,
    config: dict[str, str],
    streams: Optional[list[str]] = None,
    sync: bool = True,
) -> SourceBase:
    if name == "source-snowflake":
        return SnowflakeSource(config, streams, sync)
    if name == "source-mssql":
        return MsSqlSource(config, streams, sync)


def get_default_cache() -> DuckdbCache:
    return DuckdbCache()
