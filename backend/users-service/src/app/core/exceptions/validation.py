from typing import Any, Dict, Optional

from app.core.exceptions.base import ValidationError

class UnsupportedFileTypeError(ValidationError):
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Unsupported file type",
            code="UNSUPPORTED_FILE_TYPE",
            context=context
        )

class FileTooLargeError(ValidationError):
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="File too large",
            code="FILE_TOO_LARGE",
            context=context
        )
