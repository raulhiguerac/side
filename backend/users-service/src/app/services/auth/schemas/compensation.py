from uuid import UUID
from typing import Optional

from app.schemas.base import StrictBase
from app.models.kc_tasks import KcTaskType

class CreateKcCompensationTask(StrictBase):
    kc_user_id: UUID
    email: str
    task_type: KcTaskType
    last_error: Optional[str]
    attempts: int
