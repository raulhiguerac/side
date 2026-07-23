import uuid
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Optional

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import (
    BulkJobCreationError,
    BulkJobNotFoundError,
    RetryOfRetryNotAllowedError,
)
from app.schemas.principal import Principal
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import BulkJobCreate

_RETRY_WINDOW = timedelta(days=60)


class BulkCreatePropertiesUseCase:
    def __init__(self, *, uow: AdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        *,
        principal: Principal,
        storage_key: str,
        retry_job_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        if retry_job_id is not None:
            target_job = await run_in_threadpool(
                partial(self.uow.bulk_jobs.get_by_id, job_id=retry_job_id)
            )
            if target_job is None:
                raise BulkJobNotFoundError(job_id=retry_job_id)
            if target_job.retry_of_job_id is not None:
                raise RetryOfRetryNotAllowedError(job_id=retry_job_id)
            expiration = target_job.expires_at
        else:
            expiration = datetime.now(timezone.utc) + _RETRY_WINDOW

        batch_id = uuid.uuid4()
        data = BulkJobCreate(
            batch_id=batch_id,
            storage_key=storage_key,
            retry_of_job_id=retry_job_id,
            expiration=expiration,
            created_by=principal.sub,
        )

        try:
            await run_in_threadpool(partial(self.uow.bulk_jobs.add, data=data))
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise BulkJobCreationError(cause=exc, context={"batch_id": str(batch_id)}) from exc

        return batch_id
