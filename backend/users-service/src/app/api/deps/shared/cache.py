from functools import lru_cache

from app.integrations.cache.redis.cache import CacheClient
from app.services.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from app.services.shared.ports.cache import CachePort


@lru_cache(maxsize=1)
def get_cache_port() -> CachePort:
    return RedisCacheAdapter(CacheClient())
