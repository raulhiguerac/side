import os
from functools import lru_cache

from app.integrations.cache import CacheClient

@lru_cache
def get_cache() -> CacheClient:
    return CacheClient()