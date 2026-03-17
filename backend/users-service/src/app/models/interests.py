import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class UserInterest(SQLModel, table=True):

    __tablename__ = "user_interest"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    account_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("accounts.account_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    city_id: uuid.UUID = Field(index=True)
    is_active: bool = Field(default=True)
    deactivated_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))

    __table_args__ = (
        UniqueConstraint(
            "account_id",
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
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        )
    )
    interest_rank: int = Field(nullable=False)
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
        UniqueConstraint("user_interest_id", "neighborhood_id", name="uq_user_interest_neighborhood")
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
        )
    )
    property_type: PropertyType = Field(primary_key=True)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))