from typing import Protocol

from app.models.property import PropertyImage


class PropertyImageRepository(Protocol):
    def add(self, *, image: PropertyImage) -> None: ...
