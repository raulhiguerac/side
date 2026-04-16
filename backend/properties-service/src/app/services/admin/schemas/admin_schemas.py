import uuid
from typing import Optional

from pydantic import Field

from app.models.property import ListingStatus, VerificationStatus
from app.schemas.base import StrictBase

class VerifyPropertyRequest(StrictBase):
    verification_status: VerificationStatus
    rejection_reason: Optional[str] = Field(default=None, max_length=500)



class CreatePromotionRequest(StrictBase):
    property_id: uuid.UUID
    promoted_days: int = Field(ge=1)
    priority: int = Field(default=0, ge=0)


class GetPropertiesAdminRequest(StrictBase):
    status: Optional[ListingStatus] = None
    verification_status: Optional[VerificationStatus] = None
    owner_id: Optional[uuid.UUID] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class BulkCreatePropertyItem(StrictBase):
    pass  # TODO: define fields