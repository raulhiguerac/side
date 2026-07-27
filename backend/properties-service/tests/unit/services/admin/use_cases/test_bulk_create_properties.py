import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import (
    BulkJobCreationError,
    BulkJobExpiredError,
    BulkJobNotFoundError,
    RetryOfRetryNotAllowedError,
)
from app.schemas.principal import Principal
from app.services.admin.use_cases.bulk_create_properties import BulkCreatePropertiesUseCase

PRINCIPAL = Principal(sub=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
ORIGINAL_JOB_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
STORAGE_KEY = "admin/file.csv"


def _job(*, expires_in_days: int = 30, retry_of=None):
    job = MagicMock()
    job.id = ORIGINAL_JOB_ID
    job.expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    job.retry_of_job_id = retry_of
    return job


@pytest.fixture
def uow():
    u = MagicMock()
    u.commit = AsyncMock()
    u.rollback = AsyncMock()
    u.bulk_jobs = MagicMock()
    return u


def _patch_threadpool():
    async def _run(fn):
        return fn()

    return patch(
        "app.services.admin.use_cases.bulk_create_properties.run_in_threadpool",
        new=AsyncMock(side_effect=_run),
    )


# ---------------------------------------------------------------------------
# New job
# ---------------------------------------------------------------------------

async def test_creates_a_job_and_returns_its_batch_id(uow):
    with _patch_threadpool():
        batch_id = await BulkCreatePropertiesUseCase(uow=uow).execute(
            principal=PRINCIPAL, storage_key=STORAGE_KEY
        )

    assert isinstance(batch_id, uuid.UUID)
    data = uow.bulk_jobs.add.call_args.kwargs["data"]
    assert data.batch_id == batch_id
    assert data.storage_key == STORAGE_KEY
    assert data.retry_of_job_id is None
    assert data.created_by == PRINCIPAL.sub
    uow.commit.assert_awaited_once()


async def test_a_new_job_gets_a_fresh_retry_window(uow):
    with _patch_threadpool():
        await BulkCreatePropertiesUseCase(uow=uow).execute(principal=PRINCIPAL, storage_key=STORAGE_KEY)

    data = uow.bulk_jobs.add.call_args.kwargs["data"]
    assert data.expiration > datetime.now(timezone.utc) + timedelta(days=59)


async def test_wraps_persistence_failures(uow):
    uow.bulk_jobs.add.side_effect = Exception("db down")

    with _patch_threadpool(), pytest.raises(BulkJobCreationError):
        await BulkCreatePropertiesUseCase(uow=uow).execute(principal=PRINCIPAL, storage_key=STORAGE_KEY)

    uow.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Retry
# ---------------------------------------------------------------------------

async def test_retry_inherits_the_original_deadline(uow):
    original = _job(expires_in_days=10)
    uow.bulk_jobs.get_by_id.return_value = original

    with _patch_threadpool():
        await BulkCreatePropertiesUseCase(uow=uow).execute(
            principal=PRINCIPAL, storage_key=STORAGE_KEY, retry_job_id=ORIGINAL_JOB_ID
        )

    data = uow.bulk_jobs.add.call_args.kwargs["data"]
    # inheriting rather than renewing is what stops a chain from living forever
    assert data.expiration == original.expires_at
    assert data.retry_of_job_id == ORIGINAL_JOB_ID


async def test_retrying_an_unknown_job_raises(uow):
    uow.bulk_jobs.get_by_id.return_value = None

    with _patch_threadpool(), pytest.raises(BulkJobNotFoundError):
        await BulkCreatePropertiesUseCase(uow=uow).execute(
            principal=PRINCIPAL, storage_key=STORAGE_KEY, retry_job_id=ORIGINAL_JOB_ID
        )

    uow.bulk_jobs.add.assert_not_called()


async def test_cannot_retry_a_retry(uow):
    uow.bulk_jobs.get_by_id.return_value = _job(retry_of=uuid.uuid4())

    with _patch_threadpool(), pytest.raises(RetryOfRetryNotAllowedError):
        await BulkCreatePropertiesUseCase(uow=uow).execute(
            principal=PRINCIPAL, storage_key=STORAGE_KEY, retry_job_id=ORIGINAL_JOB_ID
        )

    uow.bulk_jobs.add.assert_not_called()


async def test_cannot_retry_past_the_window(uow):
    uow.bulk_jobs.get_by_id.return_value = _job(expires_in_days=-1)

    with _patch_threadpool(), pytest.raises(BulkJobExpiredError):
        await BulkCreatePropertiesUseCase(uow=uow).execute(
            principal=PRINCIPAL, storage_key=STORAGE_KEY, retry_job_id=ORIGINAL_JOB_ID
        )

    uow.bulk_jobs.add.assert_not_called()


async def test_retry_of_retry_wins_over_the_expiry_check(uow):
    """Both are wrong; the structural error is the more useful message."""
    uow.bulk_jobs.get_by_id.return_value = _job(expires_in_days=-1, retry_of=uuid.uuid4())

    with _patch_threadpool(), pytest.raises(RetryOfRetryNotAllowedError):
        await BulkCreatePropertiesUseCase(uow=uow).execute(
            principal=PRINCIPAL, storage_key=STORAGE_KEY, retry_job_id=ORIGINAL_JOB_ID
        )
