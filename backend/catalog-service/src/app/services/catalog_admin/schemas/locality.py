import uuid

from app.models.location import LocalityType
from app.schemas.base import StrictBase
from app.schemas.pagination import Page, PageRequest


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


class GetAllLocalitiesRequest(PageRequest):
    country_id: uuid.UUID | None = None
    admin_division_id: uuid.UUID | None = None
    is_active: bool | None = None


class LocalityPoint(StrictBase):
    latitude: float
    longitude: float


class GetAllLocalitiesResponse(StrictBase):
    id: uuid.UUID
    country_id: uuid.UUID
    admin_division_id: uuid.UUID
    code: str
    name: str
    local_name: str | None
    locality_type: LocalityType
    point: LocalityPoint
    timezone: str
    is_active: bool
    is_capital: bool


class GetAllLocalitiesPage(Page[GetAllLocalitiesResponse]):
    pass
