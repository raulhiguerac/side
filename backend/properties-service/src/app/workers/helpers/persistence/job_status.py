import logging
import uuid
from datetime import datetime, timezone
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.models.bulk_job import JobStatus
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.workers.schemas.bulk_schemas import BulkRowError

logger = logging.getLogger(__name__)


async def mark_job_failed(*, uow: AdminUnitOfWork, job_id: uuid.UUID) -> None:
    """Best-effort: the job already blew up, so a failure here is logged and
    swallowed rather than masking the original error."""
    try:
        await uow.rollback()
        await run_in_threadpool(
            partial(uow.bulk_jobs.update_status, job_id=job_id, status=JobStatus.failed)
        )
        await uow.commit()
    except Exception as exc:
        await uow.rollback()
        logger.error("failed to mark job as failed", extra={"job_id": str(job_id)}, exc_info=exc)


async def finalize_job(
        *,
        uow: AdminUnitOfWork,
        job_id: uuid.UUID,
        inserted: int,
        errors: list[BulkRowError],
    ) -> None:
    """Only reached when the run went through end to end, so this is the single
    place that stamps confirmed_at — a failed job never gets one."""
    await run_in_threadpool(
        partial(
            uow.bulk_jobs.update_status,
            job_id = job_id,
            status = JobStatus.completed,
            errors = [error.model_dump() for error in errors],
            confirmed_at = datetime.now(timezone.utc),
            inserted = inserted,
        )
    )
    await uow.commit()
