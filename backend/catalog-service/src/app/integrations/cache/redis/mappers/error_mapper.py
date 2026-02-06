from redis.exceptions import (
    RedisError,
    ResponseError,
    DataError,
    ConnectionError,
    TimeoutError,
)

from app.core.logging.logger import get_logger

logger = get_logger(__name__)


def log_cache_error(
    *,
    exc: Exception,
    operation: str,
    key: str,
    payload_type: str | None = None,
) -> None:
    """
    Centralized cache error logger.
    Cache is fail-open: this function NEVER raises.
    """

    if isinstance(exc, (ConnectionError, TimeoutError)):
        logger.warning(
            "cache_connection_failed",
            extra={
                "extra": {
                    "operation": operation,
                    "key": key,
                    "reason": exc.__class__.__name__,
                }
            },
        )
        return

    if isinstance(exc, (ResponseError, DataError)):
        logger.error(
            "cache_operation_invalid",
            extra={
                "extra": {
                    "operation": operation,
                    "key": key,
                    "payload_type": payload_type,
                    "reason": exc.__class__.__name__,
                }
            },
            exc_info=exc,
        )
        return

    if isinstance(exc, RedisError):
        logger.error(
            "cache_unexpected_error",
            extra={
                "extra": {
                    "operation": operation,
                    "key": key,
                    "reason": exc.__class__.__name__,
                }
            },
            exc_info=exc,
        )
        return

    logger.exception(
        "cache_unknown_error",
        extra={
            "extra": {
                "operation": operation,
                "key": key,
                "reason": exc.__class__.__name__,
            }
        },
    )
