import uuid
from typing import Optional

from app.schemas.base import StrictBase


class CreateCountryRequest(StrictBase):
    iso_alpha2: str
    iso_alpha3: str
    iso_numeric: str
    name: str
    official_name: Optional[str] = None
    native_name: Optional[str] = None
    phone_code: str
    currency_code: str
    default_locale: str
    default_timezone: str
    is_supported: bool = False


class UpdateCountryRequest(StrictBase):
    name: Optional[str] = None
    official_name: Optional[str] = None
    native_name: Optional[str] = None
    phone_code: Optional[str] = None
    currency_code: Optional[str] = None
    default_locale: Optional[str] = None
    default_timezone: Optional[str] = None
    is_active: Optional[bool] = None
    is_supported: Optional[bool] = None


class CountryResponse(StrictBase):
    id: uuid.UUID
    iso_alpha2: str
    iso_alpha3: str
    name: str
    phone_code: str
    currency_code: str
    default_timezone: str
    is_active: bool
    is_supported: bool
