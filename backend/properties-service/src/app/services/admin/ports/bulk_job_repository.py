import uuid
from datetime import datetime
from typing import Any, Protocol

from app.models.bulk_job import BulkJob, JobStatus
from app.services.admin.schemas.admin_schemas import BulkJobCreate


class BulkJobRepository(Protocol):
    def add(self, *, data: BulkJobCreate) -> None: ...
    def get_by_id(self, *, job_id: uuid.UUID) -> BulkJob | None: ...
    def update_status(
        self,
        *,
        job_id: uuid.UUID,
        status: JobStatus,
        errors: list[dict[str, Any]] | None = None,
        confirmed_at: datetime | None = None,
        inserted: int | None = None,
    ) -> None: ...
