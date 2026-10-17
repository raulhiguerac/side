import uuid

from app.schemas.base import StrictBase


class NeighborhoodInfo(StrictBase):
    id: uuid.UUID
    locality_id: uuid.UUID
    name: str
    h3_cells: list[str] | None


class ResolvedNeighborhood(StrictBase):
    neighborhood: NeighborhoodInfo
    latitude: float
    longitude: float


class LocationByCoordinates(StrictBase):
    neighborhood_id: uuid.UUID
    locality_id: uuid.UUID
    country_id: uuid.UUID


class PointToResolveBase(StrictBase):
    id: str
    lat: float
    lon: float


class PointToResolve(PointToResolveBase):
    cell: str


class ResolvedPoint(StrictBase):
    id: str
    location: LocationByCoordinates | None


class BulkResolveLocationsRequest(StrictBase):
    points: list[PointToResolveBase]