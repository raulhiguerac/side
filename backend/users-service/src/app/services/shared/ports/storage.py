from typing import IO, Any, Dict, Optional, Protocol

from app.services.shared.schemas.storage import UploadResult


class StoragePort(Protocol):
    async def upload_file(
        self,
        *,
        fileobj: IO[bytes],
        bucket: str,
        key: str,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> UploadResult: ...
