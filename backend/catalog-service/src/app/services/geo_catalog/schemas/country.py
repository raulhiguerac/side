import uuid

from app.schemas.base import StrictBase


class CountryListItem(StrictBase):
    id: uuid.UUID
    name: str
    iso_alpha2: str
    phone_code: str
    is_supported: bool
