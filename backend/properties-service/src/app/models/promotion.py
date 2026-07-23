import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index
from sqlmodel import Field, Relationship

from app.models.mixins import AuditMixin


class PromotedListing(AuditMixin, table=True):

    __tablename__ = "promoted_listings"

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_promoted_listing_ends_after_starts"),
        Index("ix_promoted_listings_property_id_ends_at", "property_id", "ends_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    property_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    property: Optional["Property"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "overlaps": "promotions",
        }
    )

    is_active: bool = Field(nullable=False, default=True)
    starts_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False},
    )
    ends_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False},
    )
    priority: int = Field(nullable=False, default=0)
