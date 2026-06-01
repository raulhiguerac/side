from typing import Any, Dict, Optional

from app.core.exceptions.base import BaseError


class FileTooLargeError(BaseError):
    def __init__(self, *, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="File exceeds maximum allowed size",
            code="FILE_TOO_LARGE",
            context=context,
        )


class UnsupportedFileTypeError(BaseError):
    def __init__(self, *, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Unsupported file type",
            code="UNSUPPORTED_FILE_TYPE",
            context=context,
        )
