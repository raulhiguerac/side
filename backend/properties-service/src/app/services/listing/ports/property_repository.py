from typing import Protocol

from app.models.property import Property

class PropertyRepository(Protocol):
    def add(self, property: Property) -> None: ...