import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.models.listing import ListingStatus, ListingType, PropertyCondition, PropertyType, VerificationStatus
from app.schemas.base import StrictBase

class VerifyPropertyRequest(StrictBase):
    verification_status: VerificationStatus
    rejection_reason: Optional[str] = Field(default=None, max_length=500)



class CreatePromotionRequest(StrictBase):
    property_id: uuid.UUID
    promoted_days: int = Field(ge=1)
    priority: int = Field(default=0, ge=0)


class GetPropertiesAdminRequest(StrictBase):
    status: Optional[ListingStatus] = None
    verification_status: Optional[VerificationStatus] = None
    owner_id: Optional[uuid.UUID] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SetStatusRequest(StrictBase):
    status: ListingStatus


class SetEstimatedPriceRequest(StrictBase):
    estimated_price: Decimal = Field(gt=0, decimal_places=2)


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


class BulkJobCreate(StrictBase):
    batch_id: uuid.UUID
    storage_key: str
    retry_of_job_id: Optional[uuid.UUID] = None
    expiration: datetime
    created_by: uuid.UUID