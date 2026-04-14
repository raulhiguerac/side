import uuid
from typing import Optional, Protocol

from app.models.property import ListingStatus, Property, VerificationStatus


class AdminPropertyRepository(Protocol):
    def get_by_id(self, *, property_id: uuid.UUID) -> Property | None: ...
    def get_all(
        self,
        *,
        status: Optional[ListingStatus],
        verification_status: Optional[VerificationStatus],
        owner_id: Optional[uuid.UUID],
        offset: int,
        limit: int,
    ) -> list[Property]: ...
    def hard_delete(self, *, property_id: uuid.UUID) -> None: ...