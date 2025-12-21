import uuid
from enum import Enum
from typing import Optional
from datetime import datetime

from sqlmodel import Field, SQLModel

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy import Column,UniqueConstraint,Index,CheckConstraint,ForeignKey

class UserIntent(str,Enum):
    buyer = "buyer"
    seller = "seller"
    renter = "renter"
    explorer = "explorer"

class User(SQLModel, table=True):

    __tablename__ = "users"

    user_id: uuid.UUID = Field(primary_key=True, index=True)
    email: str = Field(unique=True, max_length=255)
    name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    phone: Optional[str] = Field(default=None)
    intent: UserIntent = Field(nullable=False)
    onboarding_step: int = Field(nullable=False, default=1)
    profile_score: int = Field(nullable=False, default=0)
    is_active: bool = Field(nullable=False, default=True)
    deactivated_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))

class Country(SQLModel, table=True):

    __tablename__ = "country"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    name: str = Field(unique=True, nullable=False)
    iso2: str = Field(nullable=False)
    iso3: str = Field(nullable=False)
    phone_code: str = Field(nullable=False)
    currency: str = Field(nullable=False)
    is_active: bool = Field(nullable=False)

class City(SQLModel, table=True):

    __tablename__ = "city"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    country_id: uuid.UUID = Field(foreign_key="country.id", index=True)
    name: str = Field(nullable=False)
    state_id: str = Field(nullable=False)
    code: str = Field(nullable=False)
    latitude: float  = Field(nullable=False)
    longitude: float = Field(nullable=False)
    is_active: bool = Field(nullable=False)
    timezone: str = Field(nullable=False)

class Neighborhood(SQLModel, table=True):

    __tablename__ = "neighborhood"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    city_id: uuid.UUID = Field(foreign_key="city.id", index=True)
    name: str = Field(max_length=150, nullable=False)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    is_active: bool = Field(default=True)

    __table_args__ = (
        UniqueConstraint("city_id", "name", name="uq_neighborhood_name"),
    )


class UserInterest(SQLModel, table=True):

    __tablename__ = "user_interest"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.user_id", index=True)
    city_id: uuid.UUID = Field(foreign_key="city.id")
    is_active: bool = Field(default=True)
    deactivated_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "city_id",
            name="uq_user_interest_user_city"
        ),
    )

class UserNeighborhoodInterest(SQLModel, table=True):

    __tablename__ = "user_neighborhood_interest"

    user_interest_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user_interest.id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    neighborhood_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("neighborhood.id", ondelete="RESTRICT"),
            primary_key=True
        )
    )
    interest_rank: int
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))

    __table_args__ = (
        UniqueConstraint(
            "user_interest_id",
            "interest_rank",
            name="uq_user_interest_rank"
        ),
        Index("ix_interest_rank", "user_interest_id", "interest_rank"),
        CheckConstraint("interest_rank BETWEEN 1 AND 5", name="ck_interest_rank_range"),
    )

class PropertyType(str,Enum):
    house = "house"
    apartment = "apartment"

class UserPropertyTypeInterest(SQLModel, table=True):

    __tablename__ = "user_property_type_interest"

    user_interest_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user_interest.id", ondelete="CASCADE"),
            primary_key=True
        ),
        index=True
    )
    property_type: PropertyType = Field(primary_key=True)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))

class UserConsents(SQLModel, table=True):

    __tablename__ = "user_consents"

    user_id: uuid.UUID = Field(foreign_key="users.user_id", primary_key=True)
    terms: bool = Field(nullable=False)
    marketing: bool = Field(nullable=False)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))
