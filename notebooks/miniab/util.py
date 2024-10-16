from typing import Callable, Optional

from .base import Source
from .sources.mssql_source import MsSqlSource
from .sources.snowflake_source import SnowflakeSource

ALL_CONNECTORS: dict[str, Callable[[tuple], Source]] = {
    "source-snowflake": lambda args: SnowflakeSource(*args),
    "source-mssql": lambda args: MsSqlSource(*args),
}


def get_available_connectors() -> list[str]:
    return list(ALL_CONNECTORS)


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
