import uuid
from enum import Enum
from typing import Optional
from datetime import datetime

from sqlmodel import Field, SQLModel

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy import Column

class KcTaskType(str,Enum):
    delete_kc_user = "delete_kc_user"

class KcTaskStatus(str,Enum):
    pending = "pending"
    done = "done"
    failed = "failed"

class KcCompensationTask(SQLModel, table=True):

    __tablename__ = "kc_compensation_tasks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    task_type: KcTaskType = Field(default=KcTaskType.delete_kc_user)
    kc_user_id: uuid.UUID = Field(index=True)
    email: Optional[str] = Field(default=None, index=True)
    status: KcTaskStatus = Field(default=KcTaskStatus.pending, index=True)
    attempts: int = Field(default=0, nullable=False)
    next_retry_at: datetime = Field(
        sa_column=Column(sa.DateTime(), nullable=False, server_default=func.now(), index=True)
    )
    last_error: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now()))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(sa.DateTime(),server_default=func.now(),onupdate=func.now()))