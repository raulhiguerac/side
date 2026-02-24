from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class UploadPolicy:
    allowed_extensions: Set[str]
    max_size_bytes: int


NEIGHBORHOOD_GEOMETRY_UPLOAD_POLICY = UploadPolicy(
    allowed_extensions={".geojson", ".json"},
    max_size_bytes=5 * 1024 * 1024,  # 5MB
)
