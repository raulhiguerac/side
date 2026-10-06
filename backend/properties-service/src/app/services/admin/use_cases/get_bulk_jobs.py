from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.models.bulk_job import BulkJob
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import (
    AdminBulkJobSchema,
    AdminBulkJobsPage,
    GetBulkJobsAdminRequest,
)


class GetBulkJobsAdminUseCase:
    """The import history: what ran, how it ended, and whether it can be replayed."""

    def __init__(self, *, uow: AdminUnitOfWork) -> None:
        self.uow = uow

    @staticmethod
    def _to_schema(job: BulkJob) -> AdminBulkJobSchema:
        """Built field by field, not model_validate: error_count is derived from
        the errors array, which the row itself does not carry as a count."""
        return AdminBulkJobSchema(
            id = job.id,
            job_type = job.job_type,
            status = job.status,
            inserted = job.inserted or 0,
            error_count = len(job.errors or []),
            retry_of_job_id = job.retry_of_job_id,
            storage_key = job.storage_key,
            expires_at = job.expires_at,
            created_at = job.created_at,
            created_by = job.created_by,
        )

    async def execute(self, *, request: GetBulkJobsAdminRequest) -> AdminBulkJobsPage:
        offset = (request.page - 1) * request.page_size
        filters = {
            "status": request.status,
            "has_errors": request.has_errors,
            "created_from": request.created_from,
            "created_to": request.created_to,
        }

        # Sequential, not gathered: both calls share this UoW's Session, and a
        # SQLAlchemy Session is not safe to use from two threads at once.
        jobs = await run_in_threadpool(
            partial(self.uow.bulk_jobs.get_all, offset=offset, limit=request.page_size, **filters)
        )
        total = await run_in_threadpool(
            partial(self.uow.bulk_jobs.count_all, **filters)
        )

        return AdminBulkJobsPage(
            items = [self._to_schema(job) for job in jobs],
            total = total,
            page = request.page,
            page_size = request.page_size,
        )
