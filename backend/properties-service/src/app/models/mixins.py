import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


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
