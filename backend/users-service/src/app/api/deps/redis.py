from functools import lru_cache
from redis import asyncio as aioredis
import os

@lru_cache
def get_redis():
    return aioredis.from_url(
        url=os.getenv("REDIS_URL"),
        decode_responses=True,
    )
