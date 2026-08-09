import uuid
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Numeric
from sqlmodel import Field, Relationship

from app.models.mixins import AuditMixin
from app.models.promotion import ACTIVE_PROMOTION_PRIMARYJOIN


# =============================================================================
# ENUMS
# =============================================================================


class PropertyType(str, Enum):
    house = "house"
    apartment = "apartment"


class ListingType(str, Enum):
    sale = "sale"
    rent = "rent"


class PropertyCondition(str, Enum):
    new = "new"
    used = "used"


class ListingStatus(str, Enum):
    draft = "draft"
    active = "active"
    inactive = "inactive"
    sold = "sold"
    rented = "rented"


class Currency(str, Enum):
    COP = "COP"
    USD = "USD"
    EUR = "EUR"
    MXN = "MXN"
    PEN = "PEN"
    CLP = "CLP"
    ARS = "ARS"


class VerificationStatus(str, Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


# =============================================================================
# MODELS
# =============================================================================


class Property(AuditMixin, table=True):

    __tablename__ = "properties"

    __table_args__ = (
        Index("ix_properties_status", "status"),
        Index("ix_properties_price", "price"),
        Index("ix_properties_owner_id_status", "owner_id", "status"),
        # Apartment must declare which floor it is on
        CheckConstraint(
            "property_type != 'apartment' OR floor_number IS NOT NULL",
            name="ck_apartment_floor_number_required",
        ),
        # House must declare how many floors it has
        CheckConstraint(
            "property_type != 'house' OR total_floors IS NOT NULL",
            name="ck_house_total_floors_required",
        ),
        CheckConstraint("area_m2 > 0", name="ck_property_area_m2_positive"),
        CheckConstraint("price > 0", name="ck_property_price_positive"),
        CheckConstraint("bathrooms >= 1", name="ck_property_bathrooms_min_one"),
        CheckConstraint("bedrooms > 0", name="ck_property_bedrooms_positive"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    owner_id: uuid.UUID = Field(nullable=False, index=True)

    property_type: PropertyType = Field(nullable=False)
    listing_type: ListingType = Field(nullable=False)
    condition: PropertyCondition = Field(nullable=False)
    status: ListingStatus = Field(nullable=False, default=ListingStatus.draft)
    currency: Currency = Field(nullable=False)
    verification_status: VerificationStatus = Field(nullable=False, default=VerificationStatus.unverified)
    verified_by: Optional[uuid.UUID] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None)

    # Floors — floor_number: which floor the apt is on; total_floors: how many floors a house has
    floor_number: Optional[int] = Field(default=None)
    total_floors: Optional[int] = Field(default=None)

    area_m2: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    bedrooms: int = Field(nullable=False)
    bathrooms: Decimal = Field(sa_column=Column(Numeric(3, 1), nullable=False))
    parking_spots: int = Field(nullable=False, default=0)

    # H3 spatial index — populated on create/update from location coordinates
    # r9 ~300m cells (detail view), r7 ~5km cells (zoomed-out map)
    h3_r9: Optional[str] = Field(default=None, max_length=16, index=True)
    h3_r7: Optional[str] = Field(default=None, max_length=16, index=True)

    description: Optional[str] = Field(default=None)
    year_built: Optional[int] = Field(default=None)
    admin_fee: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(14, 2), nullable=True))
    stratum: Optional[int] = Field(default=None)
    price: Decimal = Field(sa_column=Column(Numeric(14, 2), nullable=False))

    # Estimated prices — kept separate to preserve both signals for ML training
    admin_estimated_price: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(14, 2), nullable=True))
    admin_estimated_price_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": True},
    )
    ml_estimated_price: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(14, 2), nullable=True))
    ml_estimated_price_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": True},
    )

    images: list["PropertyImage"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "order_by": "PropertyImage.display_order",
            "primaryjoin": "and_(Property.id == foreign(PropertyImage.property_id), PropertyImage.status == 'active')",
            "viewonly": True,
            "overlaps": "property",
        },
    )
    location: Optional["PropertyLocation"] = Relationship(
        back_populates="property",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
    promotions: list["PromotedListing"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "primaryjoin": ACTIVE_PROMOTION_PRIMARYJOIN,
            "viewonly": True,
            "overlaps": "property",
        }
    )


class PropertyLocation(AuditMixin, table=True):

    __tablename__ = "property_locations"

    __table_args__ = (
        # Spatial index for viewport/distance queries
        Index("ix_property_locations_gist", "location", postgresql_using="gist"),
        Index("ix_property_locations_neighborhood_id", "neighborhood_id"),
        Index("ix_property_locations_city_id", "city_id"),
        Index("ix_property_locations_country_id", "country_id"),
    )

    property_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("properties.id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    neighborhood_id: uuid.UUID = Field(nullable=False)
    city_id: uuid.UUID = Field(nullable=False)
    country_id: uuid.UUID = Field(nullable=False)
    # SRID 4326 = WGS84 (standard GPS coordinates)
    location: Any = Field(
        sa_column=Column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    )

    property: Optional["Property"] = Relationship(back_populates="location")
