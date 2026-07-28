import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field
from app.models.mixins import AuditMixin

class JobStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class JobType(str, enum.Enum):
    bulk_create_properties = "bulk_create_properties"

class BulkJob(AuditMixin, table=True):

    __tablename__ = "bulk_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    job_type: JobType = Field(nullable=False)
    status: JobStatus = Field(nullable=False, default=JobStatus.pending)
    # Rows that landed. Every row either inserts or produces an error, so this
    # plus len(errors) is the total the run read.
    inserted: int = Field(nullable=False, default=0)
    errors: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(ARRAY(JSONB), nullable=False))
    retry_of_job_id: Optional[uuid.UUID] = Field(default=None, foreign_key="bulk_jobs.id")
    storage_key: str = Field(nullable=False)
    expires_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": False},
    )
    confirmed_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"nullable": True},
    )
