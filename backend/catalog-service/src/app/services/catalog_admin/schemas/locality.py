import uuid
from typing import Optional

from app.models.location import LocalityType
from app.schemas.base import StrictBase


class CreateLocalityRequest(StrictBase):
    country_id: uuid.UUID
    admin_division_id: uuid.UUID
    code: str
    name: str
    local_name: Optional[str] = None
    locality_type: LocalityType = LocalityType.city
    latitude: float
    longitude: float
    timezone: str
    is_capital: bool = False


class UpdateLocalityRequest(StrictBase):
    name: Optional[str] = None
    local_name: Optional[str] = None
    locality_type: Optional[LocalityType] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    is_capital: Optional[bool] = None


class LocalityAdminResponse(StrictBase):
    id: uuid.UUID
    country_id: uuid.UUID
    admin_division_id: uuid.UUID
    code: str
    name: str
    local_name: Optional[str]
    locality_type: LocalityType
    latitude: float
    longitude: float
    timezone: str
    is_active: bool
    is_capital: bool
