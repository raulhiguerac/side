import uuid
from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.models.listing import ListingType, PropertyCondition, PropertyType
from app.schemas.base import StrictBase


class BulkPropertyCsvRow(StrictBase):
    """
    Raw CSV row, before catalog/owner enrichment — mirrors the header of
    seed_bogota_500.csv plus `email` (owner's account email, resolved to
    owner_id via the users-service bulk endpoint downstream).

    Fields that can carry non-numeric placeholder values in the source data
    ("Sin especificar", "Más de 10", "16 a 30 años", etc.) stay as `str` on
    purpose — they're parsed by the tolerant helpers in seed_mapper.py
    (parse_parking, parse_bathrooms, parse_stratum, ...), not here.
    """

    # Stable key of the row in the source data. The property id is derived from
    # it, so re-importing the same file upserts instead of duplicating.
    # Required and non-empty on purpose: blank values would all hash to the same
    # id and silently overwrite each other.
    external_id: str = Field(min_length=1)

    area_m2: str
    cuartos: str
    estrato: str
    tipo: str
    parqueaderos: str
    banios: str
    piso: str
    precio: str
    precio_admin: str
    tipo_propiedad: str
    lat: float
    lon: float
    antiguedad: str
    descripcion: str = ""
    image_urls: str = ""
    email: str


class BulkCreatePropertyItem(StrictBase):
    """Enriched CSV row — catalog IDs already resolved, ready for ORM construction."""

    external_id: str = Field(min_length=1)

    property_type: PropertyType
    listing_type: ListingType
    condition: PropertyCondition

    area_m2: Decimal = Field(gt=0, decimal_places=2)
    bedrooms: int = Field(ge=1)
    bathrooms: Decimal = Field(ge=1, decimal_places=1)
    parking_spots: int = Field(default=0, ge=0)
    floor_number: Optional[int] = Field(default=None, ge=0)   # required for apartments
    total_floors: Optional[int] = Field(default=None, ge=1)   # required for houses
    stratum: Optional[int] = Field(default=None, ge=1, le=6)

    price: Decimal = Field(gt=0, decimal_places=2)
    admin_fee: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    description: Optional[str] = Field(default=None, max_length=2000)
    year_built: Optional[int] = Field(default=None, ge=1800)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    # Resolved by catalog enrichment script via /v1/geo-resolution/by-coordinates
    neighborhood_id: uuid.UUID
    city_id: uuid.UUID
    country_id: uuid.UUID

    image_urls: list[str] = Field(default_factory=list)


class BulkRowError(StrictBase):
    line: int
    ref: str
    issues: list[str]


class BulkCreatePropertiesResult(StrictBase):
    inserted: int
    errors: list[BulkRowError] = Field(default_factory=list)
