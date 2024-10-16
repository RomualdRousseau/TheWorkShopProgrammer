from ..base import Cache
from .duckdb_cache import DuckdbCache


def get_default_cache(name: str = "default_cache") -> Cache:
    return DuckdbCache(name)
