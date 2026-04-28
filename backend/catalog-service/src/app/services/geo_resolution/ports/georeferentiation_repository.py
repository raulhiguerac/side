import uuid
from typing import Protocol

from app.models.location import Neighborhood


class GeoreferentiationRepository(Protocol):
    def get_neighborhood_by_coordinates(
            self,
            *,
            lat: float,
            lon: float,
            locality_id: uuid.UUID
        ) -> Neighborhood | None: ...

    def update_neighborhood_h3_cells(
            self, 
            *, 
            neighborhood_id: uuid.UUID, 
            h3_index: str
        ) -> None: ...

    def get_locality_country_code(
            self,
            *,
            locality_id: uuid.UUID
        ) -> str | None: ...

    def get_locality_coordinates(
            self,
            *,
            locality_id: uuid.UUID
        ) -> tuple[float, float] | None: ...