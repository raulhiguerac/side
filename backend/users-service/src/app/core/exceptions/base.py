from typing import Any


class BaseError(Exception):
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "INTERNAL_ERROR",
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        self.message = message
        self.code = code
        self.context = context or {}
        self.cause = cause
        super().__init__(self.message)