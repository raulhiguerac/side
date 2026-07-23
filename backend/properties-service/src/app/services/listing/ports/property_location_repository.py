from typing import Protocol

from app.models.listing import PropertyLocation

class PropertyLocationRepository(Protocol):
    def add(self, *, property: PropertyLocation) -> None: ...