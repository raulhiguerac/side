from typing import Any, Optional


class BaseError(Exception):
    """Base exception for all domain errors."""

    def __init__(
        self,
        message: str,
        code: str,
        context: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        http_status: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.cause = cause
        self.http_status = http_status
