from typing import Protocol

from app.services.listing.ports.property_image_repository import PropertyImageRepository
from app.services.listing.ports.property_location_repository import PropertyLocationRepository
from app.services.listing.ports.property_repository import PropertyRepository


class ListingUnitOfWork(Protocol):
    properties: PropertyRepository
    property_locations: PropertyLocationRepository
    property_images: PropertyImageRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def refresh(self, instance: object) -> None: ...
    async def begin_nested(self) -> None: ...
    async def rollback_to_savepoint(self) -> None: ...