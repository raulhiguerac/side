from typing import Any, Dict, Optional

from app.core.exceptions.base import BaseError


class BadRequestError(BaseError):
    def __init__(self, detail: str | None = None):
        super().__init__(
            message="Bad request",
            code="BAD_REQUEST",
            context={"detail": detail},
        )

class UnsupportedFileTypeError(BaseError):
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Unsupported file type",
            code="UNSUPPORTED_FILE_TYPE",
            context=context
        )

class FileTooLargeError(BaseError):
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="File too large",
            code="FILE_TOO_LARGE",
            context=context
        )
