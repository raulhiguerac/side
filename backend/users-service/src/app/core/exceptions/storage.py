from typing import Any, Dict, Optional
from app.core.exceptions.base import BaseError

class BucketNotFoundError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Storage bucket not found or inaccessible",
            code="BUCKET_NOT_FOUND",
            cause=cause,
            context=context
        )

class StorageUnavailableError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Storage provider unavailable",
            code="STORAGE_PROVIDER_UNAVAILABLE",
            cause=cause,
            context=context
        )

class StorageUploadFailedError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Failed to upload file to storage",
            code="STORAGE_UPLOAD_FAILED",
            cause=cause,
            context=context
        )
    
class StorageAccessDeniedError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Access denied to storage resource",
            code="STORAGE_ACCESS_DENIED",
            cause=cause,
            context=context
        )
    
class StorageMisconfiguredError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Storage provider is misconfigured",
            code="STORAGE_MISCONFIGURED",
            cause=cause,
            context=context
        )

class StorageInvalidRequestError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Invalid request to storage client",
            code="STORAGE_INVALID_REQUEST",
            cause=cause,
            context=context
        )
    
