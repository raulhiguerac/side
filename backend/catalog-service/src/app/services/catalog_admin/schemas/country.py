import uuid

from app.schemas.base import StrictBase
from app.schemas.pagination import Page, PageRequest


class CreateCountryRequest(StrictBase):
    iso_alpha2: str
    iso_alpha3: str
    iso_numeric: str
    name: str
    official_name: str | None = None
    native_name: str | None = None
    phone_code: str
    currency_code: str
    default_locale: str
    default_timezone: str
    is_supported: bool = False


class UpdateCountryRequest(StrictBase):
    name: str | None = None
    official_name: str | None = None
    native_name: str | None = None
    phone_code: str | None = None
    currency_code: str | None = None
    default_locale: str | None = None
    default_timezone: str | None = None
    is_active: bool | None = None
    is_supported: bool | None = None


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


class GetAllCountriesRequest(PageRequest):
    is_active: bool | None = None
    is_supported: bool | None = None


class GetAllCountriesResponse(StrictBase):
    id: uuid.UUID
    iso_alpha2: str
    iso_alpha3: str
    iso_numeric: str
    name: str
    official_name: str | None
    native_name: str | None
    phone_code: str
    currency_code: str
    default_locale: str
    default_timezone: str
    is_active: bool
    is_supported: bool


class GetAllCountriesPage(Page[GetAllCountriesResponse]):
    pass
