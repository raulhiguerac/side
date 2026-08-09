import uuid
from typing import Optional, Protocol

from app.models.listing import ListingStatus, Property, PropertyLocation, VerificationStatus
from app.models.image import PropertyImage


class AdminPropertyRepository(Protocol):
    def get_by_id(self, *, property_id: uuid.UUID) -> Property | None: ...
    def get_by_ids(self, *, property_ids: list[uuid.UUID]) -> list[Property]: ...
    def get_all(
        self,
        *,
        status: Optional[ListingStatus],
        verification_status: Optional[VerificationStatus],
        owner_id: Optional[uuid.UUID],
        is_promoted: Optional[bool],
        offset: int,
        limit: int,
    ) -> list[Property]: ...
    def count_all(
        self,
        *,
        status: Optional[ListingStatus],
        verification_status: Optional[VerificationStatus],
        owner_id: Optional[uuid.UUID],
        is_promoted: Optional[bool],
    ) -> int: ...
    def add(self, *, property: tuple[Property, PropertyLocation, list[PropertyImage]]) -> None: ...
    def bulk_insert(self, *, properties: list[tuple[Property, PropertyLocation, list[PropertyImage]]]) -> None: ...