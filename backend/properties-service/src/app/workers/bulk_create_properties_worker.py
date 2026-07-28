import uuid
import logging
import time
from functools import partial

from fastapi.concurrency import run_in_threadpool

from pydantic import ValidationError

from app.core.config.settings import settings
from app.core.exceptions.listing import BulkJobNotFoundError
from app.core.exceptions.storage import StorageMisconfiguredError
from app.schemas.principal import Principal
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.shared.ports.catalog_gateway import CatalogGateway
from app.services.shared.ports.users_gateway import UsersGateway
from app.services.shared.ports.storage import StoragePort
from app.services.shared.schemas.users_schemas import ResolvedAccount
from app.workers.helpers.chunking.chunk_runner import process_chunk
from app.workers.helpers.chunking.csv_stream import iter_csv_rows
from app.workers.helpers.persistence.job_status import finalize_job, mark_job_failed
from app.workers.helpers.row_ref import row_ref
from app.workers.schemas.bulk_schemas import BulkCreatePropertiesResult, BulkPropertyCsvRow, BulkRowError


logger = logging.getLogger(__name__)

_CHUNK_SIZE = 2500


class BulkCreatePropertiesWorker:
    def __init__(
            self,
            *,
            uow: AdminUnitOfWork,
            catalog: CatalogGateway,
            users: UsersGateway,
            storage: StoragePort
        ) -> None:
        self.uow = uow
        self.catalog = catalog
        self.users = users
        self.storage = storage

        if not settings.BUCKET_BULK_PROPERTIES:
            raise StorageMisconfiguredError(context={"missing": "BUCKET_BULK_PROPERTIES"})

        self.bucket = settings.BUCKET_BULK_PROPERTIES

    async def execute(
            self,
            *,
            principal: Principal,
            job_id: uuid.UUID
        ) -> None:
        """Entry point for the background task. Nobody is left to receive a return
        value, so the outcome is written back to the bulk_jobs row instead."""
        started = time.monotonic()
        logger.info(
            "background task picked up job",
            extra={"job_id": str(job_id), "principal": str(principal.sub)},
        )
        try:
            result = await self._process(principal=principal, job_id=job_id)
        except Exception as exc:
            logger.error(
                "bulk create properties failed",
                extra={"job_id": str(job_id), "elapsed_s": round(time.monotonic() - started, 2)},
                exc_info=exc,
            )
            await mark_job_failed(uow=self.uow, job_id=job_id)
            raise

        await finalize_job(
            uow = self.uow,
            job_id = job_id,
            inserted = result.inserted,
            errors = result.errors,
        )
        logger.info(
            "bulk create properties complete",
            extra={
                "job_id": str(job_id),
                "inserted": result.inserted,
                "errors": len(result.errors),
                "elapsed_s": round(time.monotonic() - started, 2),
            },
        )

    async def _process(
            self,
            *,
            principal: Principal,
            job_id: uuid.UUID
        ) -> BulkCreatePropertiesResult:
        """Streams the CSV and hands it to process_chunk in fixed-size batches.
        email_cache is the only state that spans chunks — it keeps owners
        resolved once across the whole run."""

        job = await run_in_threadpool(
            partial(self.uow.bulk_jobs.get_by_id, job_id=job_id)
        )
        if job is None:
            raise BulkJobNotFoundError(job_id=job_id)

        key = job.storage_key
        logger.info("bulk create properties start", extra={"job_id": str(job_id), "key": key})

        batch: list[dict] = []
        email_cache: dict[str, ResolvedAccount] = {}
        errors: list[BulkRowError] = []
        inserted = 0
        line = 1
        chunk_no = 0

        rows = iter_csv_rows(storage=self.storage, bucket=self.bucket, key=key)
        async for row in rows:
            line += 1
            try:
                batch.append(
                    {
                        "line": line,
                        "id": str(uuid.uuid4()),
                        "value": BulkPropertyCsvRow(**row)
                    }
                )
            except ValidationError as e:
                errors.append(
                    BulkRowError(
                        line = line,
                        ref = row_ref(row),
                        issues = [f"{err['loc'][-1]}: {err['msg']}" for err in e.errors()]
                    )
                )
                continue

            if len(batch) < _CHUNK_SIZE:
                continue

            to_process, batch = batch, []
            chunk_no += 1
            chunk_inserted, chunk_errors = await self._run_chunk(
                to_process,
                principal = principal,
                email_cache = email_cache,
                chunk_no = chunk_no,
            )
            inserted += chunk_inserted
            errors.extend(chunk_errors)

        if batch:
            chunk_no += 1
            chunk_inserted, chunk_errors = await self._run_chunk(
                batch,
                principal = principal,
                email_cache = email_cache,
                chunk_no = chunk_no,
            )
            inserted += chunk_inserted
            errors.extend(chunk_errors)

        logger.info(
            "streaming done",
            extra={
                "job_id": str(job_id),
                "lines_read": line - 1,
                "chunks": chunk_no,
                "inserted": inserted,
                "errors": len(errors),
                "owners_resolved": len(email_cache),
            },
        )

        return BulkCreatePropertiesResult(inserted=inserted, errors=errors)

    async def _run_chunk(
            self,
            rows: list[dict],
            *,
            principal: Principal,
            email_cache: dict[str, ResolvedAccount],
            chunk_no: int,
        ) -> tuple[int, list[BulkRowError]]:
        started = time.monotonic()
        logger.info("chunk start", extra={"chunk": chunk_no, "rows": len(rows)})

        inserted, chunk_errors = await process_chunk(
            rows,
            principal = principal,
            uow = self.uow,
            catalog = self.catalog,
            resolve_emails = self._process_users_batch,
            email_cache = email_cache,
        )

        logger.info(
            "chunk done",
            extra={
                "chunk": chunk_no,
                "rows": len(rows),
                "inserted": inserted,
                "errors": len(chunk_errors),
                "elapsed_s": round(time.monotonic() - started, 2),
            },
        )
        return inserted, chunk_errors

    async def _process_users_batch(self, emails: set[str]) -> list[ResolvedAccount]:
        """Resolves owner emails to account ids in one call. Emails with no active
        account simply don't come back, so their rows fail later with an
        "owner not resolved" error instead of being silently assigned."""
        started = time.monotonic()
        resolved = await self.users.resolve_accounts(emails=list(emails))
        logger.info(
            "users resolve",
            extra={
                "requested": len(emails),
                "resolved": len(resolved),
                "elapsed_s": round(time.monotonic() - started, 2),
            },
        )
        return resolved
