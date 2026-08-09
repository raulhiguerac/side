import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, and_, func
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


# Una promoción vigente es la que está activa **y** no venció. Nada apaga el
# `is_active` al llegar `ends_at` —hace falta un job que expire las vencidas, ver
# open-items— así que hasta entonces la fecha se filtra en cada lectura.
#
# Definido una sola vez y no en cada query: si una lectura se olvida del
# `ends_at`, una promoción vencida vuelve a contar como ad pago en ese camino y
# en ningún otro.
def active_promotion_clause():
    return and_(
        PromotedListing.is_active == True,  # noqa: E712
        PromotedListing.ends_at > func.now(),
    )


# La misma condición en texto, para el `primaryjoin` de `Property.promotions`,
# que se declara como string y no puede llamar a la función de arriba.
ACTIVE_PROMOTION_PRIMARYJOIN = (
    "and_("
    "Property.id == foreign(PromotedListing.property_id), "
    "PromotedListing.is_active == True, "
    "PromotedListing.ends_at > func.now()"
    ")"
)
