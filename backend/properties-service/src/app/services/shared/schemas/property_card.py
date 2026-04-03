import uuid
from decimal import Decimal
from typing import Optional

from pydantic import ConfigDict

from app.models.property import Currency, ListingStatus, ListingType, PropertyType
from app.schemas.base import StrictBase


class PropertyImageCard(StrictBase):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    url: str
    is_cover: bool
    display_order: int


class PropertyLocationCard(StrictBase):
    model_config = ConfigDict(extra="ignore", from_attributes=True)

    neighborhood_id: uuid.UUID
    city_id: uuid.UUID


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

    location: Optional[PropertyLocationCard] = None
    images: list[PropertyImageCard] = []
