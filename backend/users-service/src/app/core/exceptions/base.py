from typing import Any, Dict, Optional

class BaseError(Exception):
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.context = context or {}
        self.cause = cause
        super().__init__(self.message)
