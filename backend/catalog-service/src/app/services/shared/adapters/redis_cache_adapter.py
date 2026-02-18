from app.services.shared.ports.cache import CachePort

from app.integrations.cache.redis.cache import CacheClient

class RedisCacheAdapter(CachePort):
    """
    Adapter de infraestructura para cache.
    Implementa CachePort usando Redis.
    """

    def __init__(self, client: CacheClient) -> None:
        self._client = client

    async def get(self, *, key: str) -> str | None:
        return await self._client.get(key)

    async def getdel(self, *, key) -> str | None:
        return await self._client.get_del(key=key)

    async def set(self, *, key: str, value: str, ttl: int | None = None) -> None:
        await self._client.set(key, value, ttl)

    async def get_json(self, *, key: str) -> dict | list | None:
        return await self._client.get_json(key)

    async def getdel_json(self, *, key: str) -> dict | list | None:
        return await self._client.get_del_json(key=key)

    async def set_json(
        self,
        *,
        key: str,
        value: dict | list,
        ttl: int | None = None,
    ) -> None:
        await self._client.set_json(key, value, ttl)

    async def set_nx(self, *, key: str, value: str, ttl: int | None = None) -> bool:
        return await self._client.set_nx(key, value, ttl)

    async def delete(self, *, key: str) -> None:
        await self._client.delete(key)
