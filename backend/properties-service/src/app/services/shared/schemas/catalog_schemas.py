import uuid

from app.schemas.base import StrictBase


class NeighborhoodInfo(StrictBase):
    id: uuid.UUID
    locality_id: uuid.UUID
    name: str
