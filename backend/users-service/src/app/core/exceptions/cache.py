from typing import Any, Dict, Optional
from app.core.exceptions.base import BaseError
    
class CacheMisconfiguredError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Cache provider is misconfigured",
            code="CACHE_MISCONFIGURED",
            cause=cause,
            context=context
        )