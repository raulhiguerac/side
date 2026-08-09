import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import ConfigDict, Field, model_validator

from app.models.bulk_job import JobStatus
from app.models.listing import Currency, ListingStatus, ListingType, PropertyType, VerificationStatus
from app.schemas.base import StrictBase
from app.services.shared.schemas.property_card import PropertyCardSchema
from app.services.shared.schemas.property_detail import PropertyDetailSchema

class VerifyPropertyRequest(StrictBase):
    verification_status: VerificationStatus
    rejection_reason: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_rejection_reason(self) -> "VerifyPropertyRequest":
        """El motivo solo tiene sentido al rechazar.

        Sin esta regla el UC persiste el campo tal cual llegue: aprobar mandando
        motivo deja una fila que se contradice, y rechazar sin motivo deja al
        dueño sin saber qué corregir.
        """
        is_rejection = self.verification_status == VerificationStatus.rejected

        if is_rejection and not self.rejection_reason:
            raise ValueError("rejection_reason is required when rejecting a property")

        if not is_rejection and self.rejection_reason is not None:
            raise ValueError(
                f"rejection_reason is only allowed when rejecting, not for '{self.verification_status.value}'"
            )

        return self



class CreatePromotionRequest(StrictBase):
    property_id: uuid.UUID
    # Tope de 60 días: una promoción es una campaña, no un estado permanente.
    promoted_days: int = Field(ge=1, le=60)
    priority: int = Field(default=0, ge=0)


class GetPropertiesAdminRequest(StrictBase):
    status: Optional[ListingStatus] = None
    verification_status: Optional[VerificationStatus] = None
    owner_id: Optional[uuid.UUID] = None
    # Filtra por promoción activa, que es la condición del
    # DuplicateActivePromotionError: `false` da las promocionables.
    is_promoted: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AdminPropertyCardSchema(StrictBase):
    """Row of the moderation table.

    Deliberately not PropertyCardSchema: that one is the public-facing card used
    by the feed and the owner's list, and it hides exactly the fields moderation
    works with (verification_status, owner_id, created_at, rejection_reason).
    """

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    property_type: PropertyType
    listing_type: ListingType
    status: ListingStatus
    verification_status: VerificationStatus
    rejection_reason: Optional[str] = None
    price: Decimal
    currency: Currency
    area_m2: Decimal
    bedrooms: int
    bathrooms: Decimal
    created_at: datetime


class AdminPropertyDetailSchema(PropertyDetailSchema):
    """Detail plus the legal moderation targets for the state it is in.

    They are derived from status/verification_status, so they are computed on
    the way out — nothing to store, nothing to cache. Shipping them is what
    keeps the panel from offering a transition the use cases would reject.
    """

    allowed_verification_targets: list[VerificationStatus]
    allowed_status_targets: list[ListingStatus]


class GetPromotionsAdminRequest(StrictBase):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class AdminPromotionSchema(StrictBase):
    """A promotion, with the property it promotes nested inside.

    Deliberately not a bare PropertyCardSchema: that one answers "is it
    promoted?" and nothing else, so a panel listing promotions could not show
    priority or when they expire — the only two things a promotion decides.
    """

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    priority: int
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    property: Optional[PropertyCardSchema] = None


class AdminPromotionsPage(StrictBase):
    items: list[AdminPromotionSchema]
    total: int
    page: int
    page_size: int


class AdminPropertiesPage(StrictBase):
    """`total` needs its own COUNT — a bare list can only tell the client
    "there may be more", never how many pages there are."""

    items: list[AdminPropertyCardSchema]
    total: int
    page: int
    page_size: int


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