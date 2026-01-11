import os
import json
from redis import asyncio as aioredis

from redis.exceptions import (
    RedisError,
    ResponseError,
    DataError,
    ConnectionError,
    TimeoutError,
)
from app.core.exceptions.cache import CacheMisconfiguredError

from app.core.logging.logger import get_logger

logger = get_logger(__name__)

class CacheClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")

        if not self.redis_url:
            raise CacheMisconfiguredError(
                context={"missing": "REDIS_URL"}
            )
        
        self.client= aioredis.from_url(
            url=self.redis_url,
            decode_responses=True,
        )
    
    async def set(self, key: str, value: str, ttl: int | None = None):
        try:
            if ttl is not None:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)

        except (ConnectionError, TimeoutError):
            logger.warning(
                "cache_connection_failed",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "set",
                        "key": key,
                        "reason": "connection_error | timeout",
                    }
                },
            )
            return

        except (ResponseError, DataError) as exc:
            logger.error(
                "cache_operation_invalid",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "set",
                        "key": key,
                        "payload_type": type(value).__name__,
                        "reason": exc.__class__.__name__,
                    }
                },
                exc_info=exc,
            )
            return

        except RedisError as exc:
            logger.error(
                "cache_unexpected_error",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "set",
                        "key": key,
                    }
                },
                exc_info=exc,
            )
            return
    
    async def set_json(self, key: str, value: dict | list, ttl: int | None = None) -> None:
        try:
            payload = json.dumps(value)

            if ttl is not None:
                await self.client.setex(key, ttl, payload)
            else:
                await self.client.set(key, payload)

        except (ConnectionError, TimeoutError):
            logger.warning(
                "cache_connection_failed",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "set_json",
                        "key": key,
                        "reason": "connection_error | timeout",
                    }
                },
            )
            return

        except (TypeError, ValueError):
            logger.error(
                "cache_json_serialization_failed",
                extra={
                    "extra": {
                        "operation": "set_json",
                        "key": key,
                        "payload_type": type(value).__name__,
                    }
                },
            )
            return

        except (ResponseError, DataError) as exc:
            logger.error(
                "cache_operation_invalid",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "set_json",
                        "key": key,
                        "payload_type": type(value).__name__,
                        "reason": exc.__class__.__name__,
                    }
                },
                exc_info=exc,
            )
            return

        except RedisError as exc:
            logger.error(
                "cache_unexpected_error",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "set_json",
                        "key": key,
                    }
                },
                exc_info=exc,
            )
            return
    
    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)

        except (ConnectionError, TimeoutError):
            logger.warning(
                "cache_connection_failed",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "get",
                        "key": key,
                        "reason": "connection_error | timeout",
                    }
                },
            )
            return None

        except RedisError as exc:
            logger.error(
                "cache_unexpected_error",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "get",
                        "key": key,
                    }
                },
                exc_info=exc,
            )
            return None
    
    async def get_json(self, key: str) -> dict | list | None:
        try:
            value = await self.client.get(key)

            if value is None:
                return None

            return json.loads(value)

        except (ConnectionError, TimeoutError):
            logger.warning(
                "cache_connection_failed",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "get_json",
                        "key": key,
                        "reason": "connection_error | timeout",
                    }
                },
            )
            return None

        except json.JSONDecodeError:
            logger.error(
                "cache_json_deserialization_failed",
                extra={
                    "extra": {
                        "operation": "get_json",
                        "key": key,
                    }
                },
            )
            return None

        except RedisError as exc:
            logger.error(
                "cache_unexpected_error",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "get_json",
                        "key": key,
                    }
                },
                exc_info=exc,
            )
            return None
    
    async def delete(self, key: str) -> None:
        try:
            await self.client.delete(key)

        except (ConnectionError, TimeoutError):
            logger.warning(
                "cache_connection_failed",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "delete",
                        "key": key,
                        "reason": "connection_error | timeout",
                    }
                },
            )
            return

        except RedisError as exc:
            logger.error(
                "cache_unexpected_error",
                extra={
                    "extra": {
                        "redis_url": self.redis_url,
                        "operation": "delete",
                        "key": key,
                    }
                },
                exc_info=exc,
            )
            return

                

