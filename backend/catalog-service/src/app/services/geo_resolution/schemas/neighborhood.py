import uuid
from typing import Optional

from app.schemas.base import StrictBase


class NeighborhoodInfo(StrictBase):
    id: uuid.UUID
    locality_id: uuid.UUID
    name: str
    h3_cells: Optional[list[str]]


class ResolvedNeighborhood(StrictBase):
    neighborhood: NeighborhoodInfo
    latitude: float
    longitude: float