import uuid
from decimal import Decimal
from typing import Optional

from app.core.config.settings import settings
from pydantic import Field, field_validator

from app.models.property import Currency, ListingType, PropertyCondition, PropertyType
from app.schemas.base import StrictBase


class LocationField(StrictBase):
    neighborhood_id: uuid.UUID
    city_id: uuid.UUID
    country_id: uuid.UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CreatePropertyRequest(StrictBase):
    property_type: PropertyType
    listing_type: ListingType
    condition: PropertyCondition
    currency: Currency

    # Floors
    floor_number: Optional[int] = Field(default=None, ge=0)
    total_floors: Optional[int] = Field(default=None, ge=1)

    area_m2: Decimal = Field(gt=0, decimal_places=2)
    bedrooms: int = Field(ge=1)
    bathrooms: Decimal = Field(ge=1, decimal_places=1)
    parking_spots: int = Field(default=0, ge=0)

    price: Decimal = Field(gt=0, decimal_places=2)
    currency: Currency
    admin_fee: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)

    description: Optional[str] = Field(default=None, max_length=2000)
    year_built: Optional[int] = Field(default=None, ge=1800)
    stratum: Optional[int] = Field(default=None, ge=1, le=6)

    location: LocationField

    @field_validator("floor_number")
    @classmethod
    def validate_apartment_floor(cls, v: Optional[int], info) -> Optional[int]:
        if info.data.get("property_type") == PropertyType.apartment and v is None:
            raise ValueError("floor_number is required for apartments")
        return v

    @field_validator("total_floors")
    @classmethod
    def validate_house_floors(cls, v: Optional[int], info) -> Optional[int]:
        if info.data.get("property_type") == PropertyType.house and v is None:
            raise ValueError("total_floors is required for houses")
        return v


class UpdatePropertyRequest(StrictBase):
    property_type: Optional[PropertyType] = None
    listing_type: Optional[ListingType] = None
    condition: Optional[PropertyCondition] = None
    currency: Optional[Currency] = None
    floor_number: Optional[int] = Field(default=None, ge=0)
    total_floors: Optional[int] = Field(default=None, ge=1)
    area_m2: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    bedrooms: Optional[int] = Field(default=None, ge=1)
    bathrooms: Optional[Decimal] = Field(default=None, ge=1, decimal_places=1)
    parking_spots: Optional[int] = Field(default=None, ge=0)
    price: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    admin_fee: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    description: Optional[str] = Field(default=None, max_length=2000)
    year_built: Optional[int] = Field(default=None, ge=1800)
    stratum: Optional[int] = Field(default=None, ge=1, le=6)
    location: Optional[LocationField] = None


class PresignedUrlItem(StrictBase):
    upload_url: str
    public_url: str
    key: str


class PresignedUrlsResponse(StrictBase):
    batch_id: uuid.UUID
    items: list[PresignedUrlItem]


class PresignedUrlsRequest(StrictBase):
    property_id: uuid.UUID
    create_count: int = Field(ge=1, le=settings.MAX_IMAGES_PER_PROPERTY)


class ConfirmImagesRequest(StrictBase):
    batch_id: uuid.UUID
    confirmed_keys: list[str]


class DeleteImagesRequest(StrictBase):
    image_ids: list[uuid.UUID]
