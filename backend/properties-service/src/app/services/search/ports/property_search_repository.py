import uuid
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from app.models.property import Property, PropertyType


class PropertySearchRepository(Protocol):
    def get_properties(
        self,
        *,
        city_ids: list[uuid.UUID] | None = None,
        neighborhood_ids: list[uuid.UUID] | None = None,
        property_types: list[PropertyType] | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_area_m2: Decimal | None = None,
        max_area_m2: Decimal | None = None,
        min_bathrooms: Decimal | None = None,
        bedrooms: int | None = None,
        promoted_only: bool = False,
        # Keyset cursor: (created_at, id) del último item de la página anterior
        cursor_created_at: datetime | None = None,
        cursor_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[Property]: ...

    def get_by_bbox(
        self,
        *,
        h3_indexes: list[str],
        resolution: int
    ) -> list[Property]: ...
