import uuid
from typing import Protocol

from app.models.bulk_job import BulkJob
from app.services.admin.schemas.admin_schemas import BulkJobCreate


class BulkJobRepository(Protocol):
    def add(self, *, data: BulkJobCreate) -> None: ...
    def get_by_id(self, *, job_id: uuid.UUID) -> BulkJob | None: ...
