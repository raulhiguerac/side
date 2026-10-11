import uuid

from pydantic import Field

from app.models.location import LocalityType
from app.schemas.base import StrictBase


class CreateLocalityRequest(StrictBase):
    country_id: uuid.UUID
    admin_division_id: uuid.UUID
    code: str
    name: str
    local_name: str | None = None
    locality_type: LocalityType = LocalityType.city
    latitude: float
    longitude: float
    timezone: str
    is_capital: bool = False


class UpdateLocalityRequest(StrictBase):
    name: str | None = None
    local_name: str | None = None
    locality_type: LocalityType | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    is_active: bool | None = None
    is_capital: bool | None = None


class LocalityAdminResponse(StrictBase):
    id: uuid.UUID
    country_id: uuid.UUID
    admin_division_id: uuid.UUID
    code: str
    name: str
    local_name: str | None
    locality_type: LocalityType
    latitude: float
    longitude: float
    timezone: str
    is_active: bool
    is_capital: bool


class GetAllLocalitiesRequest(StrictBase):
    country_id: uuid.UUID | None = None
    admin_division_id: uuid.UUID | None = None
    is_active: bool | None = None
    page_size: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class GetLocalityByIdRequest(GetAllLocalitiesRequest):
    id: uuid.UUID


class LocalityPoint(StrictBase):
    latitude: float
    longitude: float


class GetAllLocalitiesResponse(StrictBase):
    id: uuid.UUID
    code: str
    name: str
    locality_type: LocalityType
    point: LocalityPoint
    is_active: bool
    is_capital: bool


class GetAllLocalitiesPage(StrictBase):
    items: list[GetAllLocalitiesResponse]
    total_items: int
