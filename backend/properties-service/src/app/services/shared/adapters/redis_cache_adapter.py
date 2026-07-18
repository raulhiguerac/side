from typing import Any

from app.integrations.cache.redis.cache import CacheClient
from app.services.shared.ports.cache import CachePort


class RedisCacheAdapter(CachePort):
    def __init__(self, client: CacheClient) -> None:
        self._client = client

    async def get(self, *, key: str) -> str | None:
        return await self._client.get(key)

    async def mget(self, *, keys: list[str]) -> list[str | None]:
        return await self._client.mget(keys)

    async def getdel(self, *, key: str) -> str | None:
        return await self._client.get_del(key=key)

    async def set(self, *, key: str, value: str, ttl: int | None = None) -> None:
        await self._client.set(key, value, ttl)

    async def delete(self, *, key: str | list[str]) -> None:
        await self._client.delete(key)

    async def delete_pattern(self, *, pattern: str) -> None:
        await self._client.delete_pattern(pattern)

    async def get_json(self, *, key: str) -> dict | list | None:
        return await self._client.get_json(key)

    async def mget_json(self, *, keys: list[str]) -> list[Any | None]:
        return await self._client.mget_json(keys)

    async def getdel_json(self, *, key: str) -> dict | list | None:
        return await self._client.get_del_json(key=key)

    async def set_json(self, *, key: str, value: dict | list, ttl: int | None = None) -> None:
        await self._client.set_json(key, value, ttl)

    async def set_nx(self, *, key: str, value: str, ttl: int | None = None) -> bool:
        return await self._client.set_nx(key, value, ttl)

    async def mset(self, *, data: dict[str, Any]) -> None:
        await self._client.mset(data)

    async def mset_json(self, *, data: dict[str, Any], ttl: int | None = None) -> None:
        await self._client.mset_json(data, ttl)
