import uuid
from typing import Optional
from datetime import datetime

from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint, Column, Index, func, DateTime
from geoalchemy2 import Geometry

class AuditMixin(SQLModel):
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )

    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )
    )

    created_by: Optional[uuid.UUID] = Field(default=None, index=True)
    updated_by: Optional[uuid.UUID] = Field(default=None, index=True)

class Country(AuditMixin, SQLModel, table=True):
    __tablename__ = "country"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(nullable=False, unique=True, max_length=80)
    iso2: str = Field(nullable=False, unique=True, max_length=2)
    iso3: str = Field(nullable=False, unique=True, max_length=3)
    phone_code: str = Field(nullable=False, max_length=8)
    currency: str = Field(nullable=False, max_length=3)
    is_active: bool = Field(default=True, nullable=False)


class City(AuditMixin, SQLModel, table=True):
    __tablename__ = "city"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    country_id: uuid.UUID = Field(foreign_key="country.id", index=True)
    name: str = Field(nullable=False, max_length=80)
    admin1_code: str = Field(nullable=False, max_length=50)
    code: str = Field(nullable=False, max_length=30)
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    timezone: str = Field(nullable=False, max_length=64)
    is_active: bool = Field(default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("country_id", "code", name="uq_city_country_id_code"),
        UniqueConstraint("country_id", "name", name="uq_city_country_id_name"),
    )

class Neighborhood(AuditMixin, SQLModel, table=True):
    __tablename__ = "neighborhood"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    city_id: uuid.UUID = Field(foreign_key="city.id", index=True)
    code: str = Field(max_length=20, nullable=False, index=True)
    name: str = Field(max_length=150, nullable=False)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    geom: Optional[str] = Field(
        sa_column=Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)
    )
    is_active: bool = Field(default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("city_id", "code", name="uq_neighborhood_city_id_code"),
        Index("ix_neighborhood_geom", "geom", postgresql_using="gist"),
    )