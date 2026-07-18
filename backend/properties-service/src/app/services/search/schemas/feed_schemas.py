import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import h3
from pydantic import Field

from app.models.property import PropertyType
from app.schemas.base import StrictBase

from app.services.shared.schemas.property_card import PropertyCardSchema

class FeedCursor(StrictBase):
    created_at: datetime
    id: uuid.UUID
    position: int = Field(ge=0)


class FeedPreferences(StrictBase):
    city_ids: list[uuid.UUID]
    neighborhood_ids: list[uuid.UUID]
    property_types: list[PropertyType]

class FeedPage(StrictBase):
    items: list[PropertyCardSchema]
    next_cursor: str | None = None


class BoundingBox(StrictBase):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    def to_polygon(self) -> h3.LatLngPoly:
        return h3.LatLngPoly(
            outer=[
                (self.min_lat, self.min_lon),
                (self.min_lat, self.max_lon),
                (self.max_lat, self.max_lon),
                (self.max_lat, self.min_lon),
                (self.min_lat, self.min_lon),
            ]
        )


class FeedFilters(StrictBase):
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_area_m2: Optional[Decimal] = None
    max_area_m2: Optional[Decimal] = None
    min_bathrooms: Optional[Decimal] = None
    bedrooms: Optional[int] = Field(default=None, ge=1)
