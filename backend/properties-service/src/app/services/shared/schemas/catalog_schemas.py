import uuid

from app.schemas.base import StrictBase


class NeighborhoodInfo(StrictBase):
    id: uuid.UUID
    locality_id: uuid.UUID
    name: str


class LocationInfo(StrictBase):
    neighborhood_id: uuid.UUID
    city_id: uuid.UUID
    country_id: uuid.UUID
