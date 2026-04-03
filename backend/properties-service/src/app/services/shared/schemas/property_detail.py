import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import ConfigDict, model_validator

from app.models.property import (
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
    admin_fee: Optional[Decimal] = None

    area_m2: Decimal
    bedrooms: int
    bathrooms: Decimal
    parking_spots: int
    floor_number: Optional[int] = None
    total_floors: Optional[int] = None

    stratum: Optional[int] = None
    description: Optional[str] = None
    year_built: Optional[int] = None

    created_at: datetime

    location: Optional[PropertyLocationDetail] = None
    images: list[PropertyImageCard] = []
