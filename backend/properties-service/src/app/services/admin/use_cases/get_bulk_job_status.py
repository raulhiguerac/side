import uuid
from datetime import datetime, timezone
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.listing import BulkJobNotFoundError
from app.models.bulk_job import JobStatus
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import BulkJobStatusResponse


class GetBulkJobStatusUseCase:
    def __init__(self, *, uow: AdminUnitOfWork) -> None:
        self.uow = uow

    @staticmethod
    def _is_stale(*, created_at: datetime) -> bool:
        age = datetime.now(timezone.utc) - created_at
        return age.total_seconds() > settings.BULK_JOB_TIMEOUT_SECONDS

    async def execute(self, *, job_id: uuid.UUID) -> BulkJobStatusResponse:
        job = await run_in_threadpool(partial(self.uow.bulk_jobs.get_by_id, job_id=job_id))
        if job is None:
            raise BulkJobNotFoundError(job_id=job_id)

        status = job.status
        # BackgroundTasks die with the process, so a job left pending past the
        # timeout will never be finalized by anyone — report it as failed.
        if status == JobStatus.pending and self._is_stale(created_at=job.created_at):
            status = JobStatus.failed
            await run_in_threadpool(
                partial(self.uow.bulk_jobs.update_status, job_id=job_id, status=status)
            )
            await self.uow.commit()

        return BulkJobStatusResponse(
            batch_id = job.id,
            status = status,
            inserted = job.inserted or 0,
            errors = job.errors or [],
        )
