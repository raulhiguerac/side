import uuid
from typing import Protocol, List

from app.models.location import Neighborhood

class NeighborhoodRepository(Protocol): 
    def get_active_by_locality_id(
        self, *, locality_id: uuid.UUID
    ) -> list[Neighborhood]: ...

    def get_active_by_id(
        self, *, neighborhood_id: uuid.UUID
    ) -> Neighborhood: ...
