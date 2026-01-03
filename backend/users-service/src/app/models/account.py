import uuid
from enum import Enum
from typing import Optional
from datetime import datetime

from sqlmodel import Field, SQLModel

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy import Column,ForeignKey

class AccountType(str,Enum):
    person = "person"
    organization = "organization"

class AccountIntent(str,Enum):
    buyer = "buyer"
    seller = "seller"
    renter = "renter"
    explorer = "explorer"

class Account(SQLModel, table=True):

    __tablename__ = "accounts"

    account_id: uuid.UUID = Field(primary_key=True, index=True)
    email: str = Field(unique=True, index=True, max_length=255)
    account_type :AccountType = Field(nullable=False)
    onboarding_step: int = Field(nullable=False, default=1)
    is_active: bool = Field(nullable=False, default=True)
    deactivated_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))

class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profile"

    account_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("accounts.account_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    phone: Optional[str] = Field(default=None)
    intent: Optional[AccountIntent] = Field(default=None)
    photo_url: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    profile_score: int = Field(nullable=False, default=0)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(), server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(), server_default=func.now(), onupdate=func.now()))

class CompanyProfile(SQLModel, table=True):
    __tablename__ = "company_profile"

    account_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("accounts.account_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    display_name: str = Field(nullable=False)
    phone: Optional[str] = Field(default=None)
    intent: Optional[AccountIntent] = Field(default=None)
    photo_url: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    profile_score: int = Field(nullable=False, default=0)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(), server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(), server_default=func.now(), onupdate=func.now()))

class AccountConsents(SQLModel, table=True):

    __tablename__ = "user_consents"

    account_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("accounts.account_id", ondelete="CASCADE"),
            primary_key=True
        )
    )
    terms: bool = Field(nullable=False)
    marketing: bool = Field(nullable=False)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))