import uuid
from typing import Optional, Protocol

from app.models.location import Locality


class LocalityAdminRepository(Protocol):
    def get_by_id(self, *, locality_id: uuid.UUID) -> Optional[Locality]: ...
    def add(self, *, locality: Locality) -> Locality: ...
