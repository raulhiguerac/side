import os
from functools import lru_cache

from app.integrations.storage import StorageClient

from app.core.exceptions.storage import StorageMisconfiguredError

@lru_cache
def get_storage() -> StorageClient:
    return StorageClient()

@lru_cache
def get_profile_photos_bucket() -> str:
    bucket = os.getenv("PROFILE_PHOTOS_BUCKET")
    if not bucket:
        raise StorageMisconfiguredError(
            context={"missing": "PROFILE_PHOTOS_BUCKET"}
        )
    return bucket

@lru_cache
def get_public_base_url() -> str:
    base_url = os.getenv("STORAGE_PUBLIC_BASE_URL")
    if not base_url:
        raise StorageMisconfiguredError(
            context={"missing": "STORAGE_PUBLIC_BASE_URL"}
        )
    return base_url