import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel

from app.models.account import OnboardingStep


class OnboardingCompletions(SQLModel, table=True):
    __tablename__ = "onboarding_completions"

    account_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("accounts.account_id", ondelete="CASCADE"),
            primary_key=True,
        )
    )

    key: OnboardingStep = Field(primary_key=True)

    completed_at: datetime = Field(
        sa_column=Column(
            sa.DateTime(),
            server_default=func.now(),
            nullable=False,
        )
    )

    __table_args__ = (
        Index("ix_onboarding_account_id", "account_id"),
    )
