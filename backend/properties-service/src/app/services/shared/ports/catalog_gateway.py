import uuid
from typing import Protocol

from app.services.shared.schemas.catalog_schemas import (
    LocationInfo,
    NeighborhoodInfo,
    PointToResolve,
    ResolvedPoint,
)


class CatalogGateway(Protocol):
    async def get_neighborhood(self, *, neighborhood_id: uuid.UUID) -> NeighborhoodInfo: ...
    async def get_location_by_point(self, *, lat: float, lon: float) -> LocationInfo: ...
    async def get_locations_bulk(self, *, points: list[PointToResolve]) -> list[ResolvedPoint]: ...
