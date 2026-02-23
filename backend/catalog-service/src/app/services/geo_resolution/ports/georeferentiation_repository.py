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

    def get_locality_country_code(
            self,
            *,
            locality_id: uuid.UUID
        ) -> str | None: ...