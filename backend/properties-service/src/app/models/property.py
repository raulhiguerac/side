import uuid
from decimal import Decimal
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Numeric
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel


# =============================================================================
# MIXINS
# =============================================================================


class AuditMixin(SQLModel):
    """Audit + soft-delete fields for all entities."""

    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now(), "nullable": False},
    )
    created_by: Optional[uuid.UUID] = Field(default=None)
    updated_by: Optional[uuid.UUID] = Field(default=None)
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": True},
    )
    deleted_by: Optional[uuid.UUID] = Field(default=None)


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


# =============================================================================
# MODELS
# =============================================================================


class Property(AuditMixin, SQLModel, table=True):

    __tablename__ = "properties"

    __table_args__ = (
        Index("ix_properties_status", "status"),
        Index("ix_properties_price", "price"),
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
        CheckConstraint("bathrooms > 0", name="ck_property_bathrooms_positive"),
        CheckConstraint("bedrooms > 0", name="ck_property_bedrooms_positive"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    owner_id: uuid.UUID = Field(nullable=False, index=True)

    property_type: PropertyType = Field(nullable=False)
    listing_type: ListingType = Field(nullable=False)
    condition: PropertyCondition = Field(nullable=False)
    status: ListingStatus = Field(nullable=False, default=ListingStatus.draft)
    currency: Currency = Field(nullable=False)

    # Floors — floor_number: which floor the apt is on; total_floors: how many floors a house has
    floor_number: Optional[int] = Field(default=None)
    total_floors: Optional[int] = Field(default=None)

    area_m2: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    bedrooms: int = Field(nullable=False)
    bathrooms: Decimal = Field(sa_column=Column(Numeric(3, 1), nullable=False))
    parking_spots: int = Field(nullable=False, default=0)

    description: Optional[str] = Field(default=None)
    year_built: Optional[int] = Field(default=None)
    admin_fee: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(14, 2), nullable=True))
    stratum: Optional[int] = Field(default=None)
    price: Decimal = Field(sa_column=Column(Numeric(14, 2), nullable=False))

    images: list["PropertyImage"] = Relationship(
        back_populates="property",
        sa_relationship_kwargs={"lazy": "selectin", "order_by": "PropertyImage.display_order"},
    )
    location: Optional["PropertyLocation"] = Relationship(
        back_populates="property",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )


class PropertyLocation(SQLModel, table=True):

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
        sa_column=Column(Geometry("POINT", srid=4326), nullable=False)
    )

    property: Optional["Property"] = Relationship(back_populates="location")


class PropertyImage(SQLModel, table=True):

    __tablename__ = "property_images"

    __table_args__ = (
        # Only one cover image per property (partial unique index)
        Index(
            "uix_property_images_cover",
            "property_id",
            unique=True,
            postgresql_where=sa.text("is_cover = true"),
        ),
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
    display_order: int = Field(nullable=False, default=0)
    is_cover: bool = Field(nullable=False, default=False)

    property: Optional["Property"] = Relationship(back_populates="images")
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )


class PromotedListing(AuditMixin, SQLModel, table=True):

    __tablename__ = "promoted_listings"

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_promoted_listing_ends_after_starts"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    property_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        )
    )
    starts_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False},
    )
    ends_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False},
    )
    priority: int = Field(nullable=False, default=0)
