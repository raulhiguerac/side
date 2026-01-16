from typing import Any, Dict, IO, Optional

from fastapi.concurrency import run_in_threadpool

from app.schemas.storage import UploadResult
from app.services.user.ports.storage import StoragePort
from app.integrations.storage.minio.storage import StorageClient


class MinioStorageAdapter(StoragePort):
    """
    Adapter de infraestructura para almacenamiento de archivos.
    Implementa StoragePort usando MinIO (S3-compatible).
    """

    def __init__(self, client: StorageClient) -> None:
        self._client = client

    async def upload_file(
        self,
        *,
        fileobj: IO[bytes],
        bucket: str,
        key: str,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> UploadResult:
        return await run_in_threadpool(
            self._client.upload_file,
            fileobj=fileobj,
            bucket=bucket,
            key=key,
            extra_args=extra_args,
        )