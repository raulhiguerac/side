import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlmodel import Field, Relationship

from app.models.mixins import AuditMixin


# =============================================================================
# ENUMS
# =============================================================================


class ImageStatus(str, Enum):
    active = "active"
    pending_delete = "pending_delete"
    deleted = "deleted"


class BatchStatus(str, Enum):
    pending = "pending"
    ready = "ready"
    confirmed = "confirmed"
    expired = "expired"
    failed = "failed"


# =============================================================================
# MODELS
# =============================================================================


class PropertyImage(AuditMixin, table=True):

    __tablename__ = "property_images"

    __table_args__ = (
        # Only one cover image per property (partial unique index)
        Index(
            "uix_property_images_cover",
            "property_id",
            unique=True,
            postgresql_where=sa.text("is_cover = true AND status = 'active'"),
        ),
        Index("ix_property_images_property_id_status", "property_id", "status"),
        Index("ix_property_images_url", "url", unique=True),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    property_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    url: str = Field(nullable=False)
    status: ImageStatus = Field(nullable=False, default=ImageStatus.active)
    display_order: int = Field(nullable=False, default=0)
    is_cover: bool = Field(nullable=False, default=False)

    property: Optional["Property"] = Relationship(sa_relationship_kwargs={"overlaps": "images"})


class PropertyImageUploadBatch(AuditMixin, table=True):

    __tablename__ = "property_image_upload_batches"

    __table_args__ = (
        Index("ix_upload_batches_property_id", "property_id"),
        Index("ix_upload_batches_owner_id", "owner_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    property_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    owner_id: uuid.UUID = Field(nullable=False)
    status: BatchStatus = Field(nullable=False, default=BatchStatus.pending)
    expected_keys: list[str] = Field(sa_column=Column(sa.ARRAY(sa.Text), nullable=False))
    expires_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False},
    )
    confirmed_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": True},
    )
