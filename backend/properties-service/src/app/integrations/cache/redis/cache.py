import json
import os
from typing import Any

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

    async def mset(self, data: dict[str, Any]) -> None:
        try:
            await self.client.mset(data)
        except Exception as exc:
            log_cache_error(exc=exc, operation="mset", key=list(data.keys()))

    async def mset_json(self, data: dict[str, Any], ttl: int | None = None) -> None:
        try:
            async with self.client.pipeline(transaction=False) as pipe:
                for key, value in data.items():
                    payload = json.dumps(value)
                    if ttl is not None:
                        pipe.setex(key, ttl, payload)
                    else:
                        pipe.set(key, payload)
                await pipe.execute()
        except Exception as exc:
            log_cache_error(exc=exc, operation="mset_json", key=list(data.keys()))

    async def set_json(self, key: str, value: dict | list, ttl: int | None = None) -> None:
        try:
            payload = json.dumps(value)
            if ttl is not None:
                await self.client.setex(key, ttl, payload)
            else:
                await self.client.set(key, payload)
        except Exception as exc:
            log_cache_error(exc=exc, operation="set_json", key=key, payload_type=type(value).__name__)

    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)
        except Exception as exc:
            log_cache_error(exc=exc, operation="get", key=key)
            return None
    
    async def mget(self, keys: list[str]) -> list[str | None]:
        try:
            return await self.client.mget(keys)
        except Exception as exc:
            log_cache_error(exc=exc, operation="mget", key=keys)
            return [None] * len(keys)

    async def mget_json(self, keys: list[str]) -> list[Any | None]:
        try:
            values = await self.client.mget(keys)
            return [json.loads(v) if v is not None else None for v in values]
        except Exception as exc:
            log_cache_error(exc=exc, operation="mget_json", key=keys)
            return [None] * len(keys)

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

    async def set_nx(self, key: str, value: str, ttl: int | None = None) -> bool:
        try:
            return await self.client.set(key, value, nx=True, ex=ttl)
        except Exception as exc:
            log_cache_error(exc=exc, operation="set_nx", key=key, payload_type=type(value).__name__)
            return False

    async def delete(self, key: str | list[str]) -> None:
        try:
            keys = key if isinstance(key, list) else [key]
            await self.client.delete(*keys)
        except Exception as exc:
            log_cache_error(exc=exc, operation="delete", key=key)
