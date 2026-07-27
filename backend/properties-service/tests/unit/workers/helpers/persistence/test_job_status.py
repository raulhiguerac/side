import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.bulk_job import JobStatus
from app.workers.helpers.persistence.job_status import finalize_job, mark_job_failed
from app.workers.schemas.bulk_schemas import BulkRowError

JOB_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


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
        "app.workers.helpers.persistence.job_status.run_in_threadpool",
        new=AsyncMock(side_effect=_run),
    )


def _update_kwargs(uow):
    return uow.bulk_jobs.update_status.call_args.kwargs


# ---------------------------------------------------------------------------
# finalize_job
# ---------------------------------------------------------------------------

async def test_finalize_marks_completed_and_stamps_confirmed_at(uow):
    with _patch_threadpool():
        await finalize_job(uow=uow, job_id=JOB_ID, errors=[])

    kwargs = _update_kwargs(uow)
    assert kwargs["job_id"] == JOB_ID
    assert kwargs["status"] == JobStatus.completed
    assert kwargs["confirmed_at"] is not None
    uow.commit.assert_awaited_once()


async def test_finalize_serializes_row_errors_for_the_jsonb_column(uow):
    errors = [
        BulkRowError(line=2, ref="a@test.com @ 4.6,-74.0", issues=["owner not resolved"]),
        BulkRowError(line=9, ref="b@test.com @ 4.7,-74.1", issues=["bad lat/lon"]),
    ]

    with _patch_threadpool():
        await finalize_job(uow=uow, job_id=JOB_ID, errors=errors)

    persisted = _update_kwargs(uow)["errors"]
    assert persisted == [
        {"line": 2, "ref": "a@test.com @ 4.6,-74.0", "issues": ["owner not resolved"]},
        {"line": 9, "ref": "b@test.com @ 4.7,-74.1", "issues": ["bad lat/lon"]},
    ]


async def test_a_run_with_errors_still_completes(uow):
    """`completed` means the run finished, not that every row succeeded."""
    with _patch_threadpool():
        await finalize_job(uow=uow, job_id=JOB_ID, errors=[BulkRowError(line=2, ref="x", issues=["y"])])

    assert _update_kwargs(uow)["status"] == JobStatus.completed


# ---------------------------------------------------------------------------
# mark_job_failed
# ---------------------------------------------------------------------------

async def test_mark_failed_rolls_back_first_then_updates(uow):
    with _patch_threadpool():
        await mark_job_failed(uow=uow, job_id=JOB_ID)

    uow.rollback.assert_awaited_once()
    assert _update_kwargs(uow)["status"] == JobStatus.failed
    uow.commit.assert_awaited_once()


async def test_mark_failed_never_stamps_confirmed_at_or_wipes_errors(uow):
    with _patch_threadpool():
        await mark_job_failed(uow=uow, job_id=JOB_ID)

    kwargs = _update_kwargs(uow)
    assert "confirmed_at" not in kwargs
    assert "errors" not in kwargs


async def test_mark_failed_swallows_its_own_failure(uow):
    """The job already blew up — this must not mask the original exception."""
    async def _boom(fn):
        raise Exception("db is gone")

    with patch(
        "app.workers.helpers.persistence.job_status.run_in_threadpool",
        new=AsyncMock(side_effect=_boom),
    ):
        await mark_job_failed(uow=uow, job_id=JOB_ID)  # does not raise

    assert uow.rollback.await_count == 2  # the pre-update one + the recovery one
