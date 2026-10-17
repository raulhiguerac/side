import uuid

from app.schemas.base import StrictBase
from app.schemas.pagination import Page, PageRequest


class CreateAdminDivisionRequest(StrictBase):
    country_id: uuid.UUID
    code: str
    iso_code: str | None = None
    name: str
    type_name: str


class UpdateAdminDivisionRequest(StrictBase):
    name: str | None = None
    type_name: str | None = None
    iso_code: str | None = None
    is_active: bool | None = None


class AdminDivisionResponse(StrictBase):
    id: uuid.UUID
    country_id: uuid.UUID
    code: str
    iso_code: str | None
    name: str
    type_name: str
    is_active: bool


class GetAllAdminDivisionsRequest(PageRequest):
    country_id: uuid.UUID | None = None
    is_active: bool | None = None


class GetAllAdminDivisionsPage(Page[AdminDivisionResponse]):
    pass
