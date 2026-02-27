import uuid
from typing import Optional

from app.schemas.base import StrictBase


class CreateNeighborhoodRequest(StrictBase):
    locality_id: uuid.UUID
    code: str
    name: str
    postal_code: Optional[str] = None
    latitude: float
    longitude: float


class UpdateNeighborhoodRequest(StrictBase):
    name: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None


class NeighborhoodAdminResponse(StrictBase):
    id: uuid.UUID
    locality_id: uuid.UUID
    code: str
    name: str
    postal_code: Optional[str]
    latitude: float
    longitude: float
    is_active: bool


class BulkCreateNeighborhoodsResult(StrictBase):
    created: int
    errors: list[str]


class BulkEnrichNeighborhoodGeometriesResult(StrictBase):
    matched: int
    unmatched: list[str]
    updated: int
