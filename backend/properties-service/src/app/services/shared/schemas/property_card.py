import uuid
from decimal import Decimal
from typing import Any, Optional

from pydantic import ConfigDict, Field, model_validator

from app.models.property import Currency, ListingStatus, ListingType, PropertyType
from app.schemas.base import StrictBase
from app.services.shared.helpers.geometry import point_to_lat_lon


class PropertyImageCard(StrictBase):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    url: str
    is_cover: bool
    display_order: int


class PropertyLocationCard(StrictBase):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    neighborhood_id: uuid.UUID
    city_id: uuid.UUID
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def extract_coordinates(cls, data: Any) -> Any:
        if hasattr(data, "location") and data.location is not None:
            try:
                lat, lon = point_to_lat_lon(data.location)
                data.__dict__["latitude"] = lat
                data.__dict__["longitude"] = lon
            except Exception:
                pass
        return data


class PropertyCardSchema(StrictBase):
    """Public-facing card schema — used by listing (my properties) and search (feed)."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: uuid.UUID
    property_type: PropertyType
    listing_type: ListingType
    status: ListingStatus

    price: Decimal
    currency: Currency

    area_m2: Decimal
    bedrooms: int
    bathrooms: Decimal
    parking_spots: int

    is_promoted: bool = False

    location: Optional[PropertyLocationCard] = None
    images: list[PropertyImageCard] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def compute_is_promoted(cls, data: Any) -> Any:
        if hasattr(data, "promotions"):
            data.__dict__["is_promoted"] = bool(data.promotions)
        return data
