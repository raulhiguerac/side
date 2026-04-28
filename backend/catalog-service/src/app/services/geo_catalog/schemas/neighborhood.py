import uuid

from app.schemas.base import StrictBase


class NeighborhoodListItem(StrictBase):
    id: uuid.UUID
    locality_id: uuid.UUID
    name: str
    search_name: str
    latitude: float
    longitude: float


class NeighborhoodsByLocalityResponse(StrictBase):
    neighborhoods: dict[str, list[NeighborhoodListItem]]