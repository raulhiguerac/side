import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.models.property import EstimatedPriceSource, ListingStatus, VerificationStatus
from app.schemas.base import StrictBase

class VerifyPropertyRequest(StrictBase):
    verification_status: VerificationStatus
    rejection_reason: Optional[str] = Field(default=None, max_length=500)


class SetEstimatedPriceRequest(StrictBase):
    estimated_price: Decimal = Field(gt=0, decimal_places=2)
    source: EstimatedPriceSource = EstimatedPriceSource.admin


class CreatePromotionRequest(StrictBase):
    property_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    priority: int = Field(default=0, ge=0)


class GetPropertiesAdminRequest(StrictBase):
    status: Optional[ListingStatus] = None
    verification_status: Optional[VerificationStatus] = None
    owner_id: Optional[uuid.UUID] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class BulkCreatePropertyItem(StrictBase):
    pass  # TODO: define fields