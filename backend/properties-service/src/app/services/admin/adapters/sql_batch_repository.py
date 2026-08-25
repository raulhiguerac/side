import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import update
from sqlmodel import Session, func, select

from app.models.bulk_job import BulkJob, JobStatus, JobType
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

    def get_all(
        self,
        *,
        status: JobStatus | None = None,
        has_errors: bool | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[BulkJob]:
        stmt = select(BulkJob).where(BulkJob.deleted_at.is_(None))
        if status:
            stmt = stmt.where(BulkJob.status == status)
        if has_errors is not None:
            # cardinality y no array_length: sobre un array vacío da 0, no NULL.
            dropped_rows = func.cardinality(BulkJob.errors) > 0
            stmt = stmt.where(dropped_rows if has_errors else ~dropped_rows)
        if created_from is not None:
            stmt = stmt.where(BulkJob.created_at >= created_from)
        if created_to is not None:
            stmt = stmt.where(BulkJob.created_at <= created_to)

        # Sin orden explícito Postgres no garantiza ninguno, y paginar sobre eso
        # repite o se salta filas entre páginas.
        stmt = stmt.order_by(BulkJob.created_at.desc()).offset(offset).limit(limit)

        return list(self.session.exec(stmt).all())

    def count_all(
        self,
        *,
        status: JobStatus | None = None,
        has_errors: bool | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(BulkJob).where(BulkJob.deleted_at.is_(None))

        if status is not None:
            stmt = stmt.where(BulkJob.status == status)
        if has_errors is not None:
            # cardinality y no array_length: sobre un array vacío da 0, no NULL.
            dropped_rows = func.cardinality(BulkJob.errors) > 0
            stmt = stmt.where(dropped_rows if has_errors else ~dropped_rows)
        if created_from is not None:
            stmt = stmt.where(BulkJob.created_at >= created_from)
        if created_to is not None:
            stmt = stmt.where(BulkJob.created_at <= created_to)

        return self.session.exec(stmt).one()

    def update_status(
        self,
        *,
        job_id: uuid.UUID,
        status: JobStatus,
        errors: list[dict[str, Any]] | None = None,
        confirmed_at: datetime | None = None,
        inserted: int | None = None,
    ) -> None:
        # Only the columns actually passed are written, so marking a job failed
        # can't wipe errors already recorded, nor blank out confirmed_at.
        values: dict[str, Any] = {"status": status}
        if errors is not None:
            values["errors"] = errors
        if confirmed_at is not None:
            values["confirmed_at"] = confirmed_at
        if inserted is not None:
            values["inserted"] = inserted

        stmt = update(BulkJob).where(BulkJob.id == job_id).values(**values)
        self.session.exec(stmt)
        self.session.flush()
