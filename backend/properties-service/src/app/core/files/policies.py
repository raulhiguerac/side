from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class UploadPolicy:
    allowed_extensions: Set[str]
    max_size_bytes: int


PROPERTIES_BULK_UPLOAD_POLICY = UploadPolicy(
    allowed_extensions={".csv"},
    max_size_bytes=50 * 1024 * 1024,  # 50MB
)
