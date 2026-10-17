import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from app.models.listing import (
    Currency,
    ListingStatus,
    ListingType,
    PropertyCondition,
    PropertyType,
    VerificationStatus,
)
from app.schemas.base import StrictBase
from app.services.shared.helpers.geometry import point_to_lat_lon
from app.services.shared.schemas.property_card import PropertyImageCard


class PropertyLocationDetail(StrictBase):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    neighborhood_id: uuid.UUID
    city_id: uuid.UUID
    country_id: uuid.UUID
    latitude: float
    longitude: float

    @model_validator(mode="before")
    @classmethod
    def extract_coordinates(cls, data: Any) -> Any:
        if hasattr(data, "location") and data.location is not None:
            lat, lon = point_to_lat_lon(data.location)
            data.__dict__["latitude"] = lat
            data.__dict__["longitude"] = lon
        return data


class PropertyDetailSchema(StrictBase):
    """Full property schema for detail view."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: uuid.UUID
    property_type: PropertyType
    listing_type: ListingType
    condition: PropertyCondition
    status: ListingStatus
    verification_status: VerificationStatus

    price: Decimal
    currency: Currency
    admin_fee: Decimal | None = None

    area_m2: Decimal
    bedrooms: int
    bathrooms: Decimal
    parking_spots: int
    floor_number: int | None = None
    total_floors: int | None = None

    stratum: int | None = None
    description: str | None = None
    year_built: int | None = None

    created_at: datetime

    location: PropertyLocationDetail | None = None
    images: list[PropertyImageCard] = Field(default_factory=list)
