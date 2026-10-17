from typing import IO, Any, Protocol

from app.services.shared.schemas.storage import UploadResult


class StoragePort(Protocol):
    async def upload_file(
        self,
        *,
        fileobj: IO[bytes],
        bucket: str,
        key: str,
        extra_args: dict[str, Any] | None = None,
    ) -> UploadResult: ...
