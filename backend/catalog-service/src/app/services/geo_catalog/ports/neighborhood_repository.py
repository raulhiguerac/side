import uuid
from typing import Protocol

from app.models.location import Neighborhood


class NeighborhoodRepository(Protocol): 
    def get_active_by_locality_ids(
        self, *, locality_ids: list[uuid.UUID]
    ) -> list[Neighborhood]: ...

    def get_active_by_id(
        self, *, neighborhood_id: uuid.UUID
    ) -> Neighborhood: ...
