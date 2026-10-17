import uuid
from typing import Protocol

from app.models.image import PropertyImage
from app.models.listing import (
    ListingStatus,
    Property,
    PropertyLocation,
    VerificationStatus,
)


class AdminPropertyRepository(Protocol):
    def get_by_id(self, *, property_id: uuid.UUID) -> Property | None: ...
    def get_by_ids(self, *, property_ids: list[uuid.UUID]) -> list[Property]: ...
    def get_all(
        self,
        *,
        status: ListingStatus | None,
        verification_status: VerificationStatus | None,
        owner_id: uuid.UUID | None,
        is_promoted: bool | None,
        offset: int,
        limit: int,
    ) -> list[Property]: ...
    def count_all(
        self,
        *,
        status: ListingStatus | None,
        verification_status: VerificationStatus | None,
        owner_id: uuid.UUID | None,
        is_promoted: bool | None,
    ) -> int: ...
    def add(self, *, property: tuple[Property, PropertyLocation, list[PropertyImage]]) -> None: ...
    def bulk_insert(self, *, properties: list[tuple[Property, PropertyLocation, list[PropertyImage]]]) -> None: ...