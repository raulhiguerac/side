import os
import json
from redis import asyncio as aioredis

from app.core.exceptions.cache import CacheMisconfiguredError
from app.core.logging.logger import get_logger
from app.integrations.cache.redis.mappers.error_mapper import log_cache_error

logger = get_logger(__name__)


class CacheClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        if not self.redis_url:
            raise CacheMisconfiguredError(context={"missing": "REDIS_URL"})

        self.client = aioredis.from_url(
            url=self.redis_url,
            decode_responses=True,
        )

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        try:
            if ttl is not None:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
        except Exception as exc:
            log_cache_error(exc=exc, operation="set", key=key, payload_type=type(value).__name__)
            return

    async def set_json(self, key: str, value: dict | list, ttl: int | None = None) -> None:
        try:
            payload = json.dumps(value)
            if ttl is not None:
                await self.client.setex(key, ttl, payload)
            else:
                await self.client.set(key, payload)
        except Exception as exc:
            log_cache_error(exc=exc, operation="set_json", key=key, payload_type=type(value).__name__)
            return

    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)
        except Exception as exc:
            log_cache_error(exc=exc, operation="get", key=key)
            return None

    async def get_json(self, key: str) -> dict | list | None:
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as exc:
            log_cache_error(exc=exc, operation="get_json", key=key)
            return None
    
    async def get_del(self, key: str) -> str | None:
        try:
            return await self.client.getdel(key)
        except Exception as exc:
            log_cache_error(exc=exc, operation="getdel", key=key)
            return None


    async def get_del_json(self, key: str) -> dict | list | None:
        try:
            value = await self.client.getdel(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as exc:
            log_cache_error(exc=exc, operation="getdel_json", key=key)
            return None

    async def delete(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception as exc:
            log_cache_error(exc=exc, operation="delete", key=key)
            return