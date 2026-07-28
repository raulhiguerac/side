import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import BulkJobNotFoundError
from app.models.bulk_job import JobStatus
from app.services.admin.use_cases.get_bulk_job_status import GetBulkJobStatusUseCase

JOB_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _job(*, status: JobStatus, age_seconds: int = 0, errors=None, inserted=0):
    job = MagicMock()
    job.id = JOB_ID
    job.status = status
    job.created_at = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    job.errors = errors
    job.inserted = inserted
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
        "app.services.admin.use_cases.get_bulk_job_status.run_in_threadpool",
        new=AsyncMock(side_effect=_run),
    )


async def test_reports_a_completed_job_with_its_errors(uow):
    uow.bulk_jobs.get_by_id.return_value = _job(
        status=JobStatus.completed, errors=[{"line": 2, "ref": "x", "issues": ["y"]}]
    )

    with _patch_threadpool():
        result = await GetBulkJobStatusUseCase(uow=uow).execute(job_id=JOB_ID)

    assert result.batch_id == JOB_ID
    assert result.status == JobStatus.completed
    assert result.errors == [{"line": 2, "ref": "x", "issues": ["y"]}]
    uow.commit.assert_not_awaited()


async def test_reports_how_many_rows_landed(uow):
    """inserted + len(errors) is the total the run read — without it the caller
    sees a list of failures with no denominator."""
    uow.bulk_jobs.get_by_id.return_value = _job(
        status=JobStatus.completed,
        inserted=18_051,
        errors=[{"line": n, "ref": "x", "issues": ["y"]} for n in range(3)],
    )

    with _patch_threadpool():
        result = await GetBulkJobStatusUseCase(uow=uow).execute(job_id=JOB_ID)

    assert result.inserted == 18_051
    assert result.inserted + len(result.errors) == 18_054


async def test_null_errors_become_an_empty_list(uow):
    uow.bulk_jobs.get_by_id.return_value = _job(status=JobStatus.completed, errors=None)

    with _patch_threadpool():
        result = await GetBulkJobStatusUseCase(uow=uow).execute(job_id=JOB_ID)

    assert result.errors == []


async def test_unknown_job_raises(uow):
    uow.bulk_jobs.get_by_id.return_value = None

    with _patch_threadpool(), pytest.raises(BulkJobNotFoundError):
        await GetBulkJobStatusUseCase(uow=uow).execute(job_id=JOB_ID)


async def test_a_recent_pending_job_stays_pending(uow):
    uow.bulk_jobs.get_by_id.return_value = _job(status=JobStatus.pending, age_seconds=5)

    with _patch_threadpool():
        result = await GetBulkJobStatusUseCase(uow=uow).execute(job_id=JOB_ID)

    assert result.status == JobStatus.pending
    uow.bulk_jobs.update_status.assert_not_called()


async def test_a_stale_pending_job_is_reported_and_persisted_as_failed(uow, monkeypatch):
    """BackgroundTasks die with the process, so nothing else would ever
    move this row out of pending."""
    from app.core.config.settings import settings

    monkeypatch.setattr(settings, "BULK_JOB_TIMEOUT_SECONDS", 600)
    uow.bulk_jobs.get_by_id.return_value = _job(status=JobStatus.pending, age_seconds=601)

    with _patch_threadpool():
        result = await GetBulkJobStatusUseCase(uow=uow).execute(job_id=JOB_ID)

    assert result.status == JobStatus.failed
    assert uow.bulk_jobs.update_status.call_args.kwargs["status"] == JobStatus.failed
    uow.commit.assert_awaited_once()


async def test_a_stale_completed_job_is_left_alone(uow, monkeypatch):
    from app.core.config.settings import settings

    monkeypatch.setattr(settings, "BULK_JOB_TIMEOUT_SECONDS", 600)
    uow.bulk_jobs.get_by_id.return_value = _job(status=JobStatus.completed, age_seconds=99999)

    with _patch_threadpool():
        result = await GetBulkJobStatusUseCase(uow=uow).execute(job_id=JOB_ID)

    assert result.status == JobStatus.completed
    uow.bulk_jobs.update_status.assert_not_called()
