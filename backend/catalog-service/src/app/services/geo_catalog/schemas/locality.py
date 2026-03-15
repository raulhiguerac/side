import uuid

from app.schemas.base import StrictBase


class AdminDivisionRef(StrictBase):
    id: uuid.UUID
    name: str


class LocalityListItem(StrictBase):
    id: uuid.UUID
    name: str
    admin_division: AdminDivisionRef
