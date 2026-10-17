from typing import Any


class BaseError(Exception):
    """Base exception for all domain errors."""

    def __init__(
        self,
        message: str,
        code: str,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
        http_status: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.cause = cause
        self.http_status = http_status
