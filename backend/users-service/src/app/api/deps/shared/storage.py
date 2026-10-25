import os
from functools import lru_cache

from app.core.exceptions.storage import StorageMisconfiguredError
from app.integrations.storage.minio.storage import StorageClient
from app.services.shared.adapters.minio_storage_adapter import MinioStorageAdapter
from app.services.shared.ports.storage import StoragePort


@lru_cache(maxsize=1)
def get_storage_port() -> StoragePort:
    return MinioStorageAdapter(StorageClient())


@lru_cache(maxsize=1)
def get_profile_photos_bucket() -> str:
    bucket = os.getenv("PROFILE_PHOTOS_BUCKET")
    if not bucket:
        raise StorageMisconfiguredError(
            context={"missing": "PROFILE_PHOTOS_BUCKET"}
        )
    return bucket


@lru_cache(maxsize=1)
def get_public_base_url() -> str:
    base_url = os.getenv("STORAGE_PUBLIC_BASE_URL")
    if not base_url:
        raise StorageMisconfiguredError(
            context={"missing": "STORAGE_PUBLIC_BASE_URL"}
        )
    return base_url
