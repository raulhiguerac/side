import uuid
from typing import Protocol

from app.models.location import PointOfInterest


class PoiRepository(Protocol):
    def get_by_mapbox_id(self, *, mapbox_id: str) -> PointOfInterest | None: ...

    def get_active_by_locality_id(self, *, locality_id: uuid.UUID) -> list[PointOfInterest]: ...

    def search_by_name(self, *, search_name: str, locality_id: uuid.UUID) -> list[PointOfInterest]: ...

    def save(self, *, poi: PointOfInterest) -> PointOfInterest: ...
