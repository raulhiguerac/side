import uuid
from typing import Optional

from app.schemas.base import StrictBase


class CreateAdminDivisionRequest(StrictBase):
    country_id: uuid.UUID
    code: str
    iso_code: Optional[str] = None
    name: str
    type_name: str


class UpdateAdminDivisionRequest(StrictBase):
    name: Optional[str] = None
    type_name: Optional[str] = None
    iso_code: Optional[str] = None
    is_active: Optional[bool] = None


class AdminDivisionResponse(StrictBase):
    id: uuid.UUID
    country_id: uuid.UUID
    code: str
    iso_code: Optional[str]
    name: str
    type_name: str
    is_active: bool
