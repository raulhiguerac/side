import uuid
from typing import Optional, Protocol

from app.models.location import Neighborhood


class NeighborhoodAdminRepository(Protocol):
    def get_by_id(self, *, neighborhood_id: uuid.UUID) -> Optional[Neighborhood]: ...
    def add(self, *, neighborhood: Neighborhood) -> Neighborhood: ...
