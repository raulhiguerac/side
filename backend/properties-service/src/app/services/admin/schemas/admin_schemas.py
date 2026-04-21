import uuid
from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.models.property import ListingStatus, ListingType, PropertyCondition, PropertyType, VerificationStatus
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