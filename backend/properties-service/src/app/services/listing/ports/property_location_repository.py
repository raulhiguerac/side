from typing import Protocol

from app.models.property import PropertyLocation

class PropertyLocationRepository(Protocol):
    def add(self, property: PropertyLocation) -> None: ...