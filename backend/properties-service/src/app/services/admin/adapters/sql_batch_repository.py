import uuid

from sqlmodel import Session, select

from app.models.bulk_job import BulkJob, JobType
from app.services.admin.ports.bulk_job_repository import BulkJobRepository
from app.services.admin.schemas.admin_schemas import BulkJobCreate

class SqlBatchRepository(BulkJobRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, *, data: BulkJobCreate) -> None:
        self.session.add(
            BulkJob(
                id = data.batch_id,
                job_type = JobType.bulk_create_properties,
                retry_of_job_id = data.retry_of_job_id,
                storage_key = data.storage_key,
                expires_at = data.expiration,
                created_by = data.created_by,
                updated_by = data.created_by,
            )
        )
        self.session.flush()

    def get_by_id(self, *, job_id: uuid.UUID) -> BulkJob | None:
        return self.session.get(BulkJob, job_id)
