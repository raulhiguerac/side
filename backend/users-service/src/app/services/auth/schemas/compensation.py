from typing import Optional
from uuid import UUID

from app.models.kc_tasks import KcTaskType
from app.schemas.base import StrictBase


class CreateKcCompensationTask(StrictBase):
    kc_user_id: UUID
    email: str
    task_type: KcTaskType
    last_error: Optional[str]
    attempts: int
