import uuid
from typing import Optional, Protocol

from app.models.location import Neighborhood
from app.services.geo_resolution.schemas.neighborhood import (
    LocationByCoordinates,
    PointToResolve,
    ResolvedPoint,
)


class GeoreferentiationRepository(Protocol):
    def get_neighborhood_by_coordinates(
            self,
            *,
            lat: float,
            lon: float,
            locality_id: uuid.UUID
        ) -> Neighborhood | None: ...

    def get_location_by_point(
            self,
            *,
            lat: float,
            lon: float,
            cell: str
        ) -> Optional[LocationByCoordinates]: ...

    def get_location_by_points(
            self,
            *,
            points: list[PointToResolve],
        ) -> list[ResolvedPoint]: ...

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