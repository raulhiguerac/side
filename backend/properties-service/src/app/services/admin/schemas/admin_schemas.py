import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import Field

from app.models.bulk_job import JobStatus
from app.models.listing import ListingStatus, VerificationStatus
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


class SetStatusRequest(StrictBase):
    status: ListingStatus


class SetEstimatedPriceRequest(StrictBase):
    estimated_price: Decimal = Field(gt=0, decimal_places=2)


class BulkJobCreate(StrictBase):
    batch_id: uuid.UUID
    storage_key: str
    retry_of_job_id: Optional[uuid.UUID] = None
    expiration: datetime
    created_by: uuid.UUID


class BulkUploadUrlRequest(StrictBase):
    filename: str = Field(min_length=1)


class BulkUploadUrlResponse(StrictBase):
    """`max_size_bytes` is advisory — a plain presigned PUT can't cap the body
    size, so the front pre-checks and the worker streams rather than trusting it."""

    storage_key: str
    upload_url: str
    max_size_bytes: int
    expires_in: int


class BulkCreatePropertiesRequest(StrictBase):
    """The front uploads the CSV straight to storage with a presigned PUT, so the
    endpoint only receives the resulting key — never the file itself."""

    storage_key: str
    retry_of_job_id: Optional[uuid.UUID] = None


class BulkJobAccepted(StrictBase):
    batch_id: uuid.UUID


class BulkJobStatusResponse(StrictBase):
    batch_id: uuid.UUID
    status: JobStatus
    # Every row either lands or produces an error, so inserted + len(errors)
    # is the total the run read.
    inserted: int = 0
    errors: list[dict[str, Any]] = Field(default_factory=list)