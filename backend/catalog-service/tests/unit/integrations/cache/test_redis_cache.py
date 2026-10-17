from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError

from app.integrations.cache.redis.cache import CacheClient


@pytest.fixture
def cache(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    client = CacheClient()
    client.client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_get_json_returns_none_when_redis_fails(cache):
    cache.client.get.side_effect = ConnectionError("Redis down")

    assert await cache.get_json(key="k") is None


@pytest.mark.asyncio
async def test_set_json_swallows_redis_failure(cache):
    cache.client.setex.side_effect = ConnectionError("Redis down")

    await cache.set_json(key="k", value={"lat": 1.0}, ttl=60)

    cache.client.setex.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_json_decodes_cached_value(cache):
    cache.client.get.return_value = '{"lat": 1.0}'

    assert await cache.get_json(key="k") == {"lat": 1.0}
