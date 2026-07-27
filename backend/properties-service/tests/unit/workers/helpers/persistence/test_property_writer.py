import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.helpers.persistence.property_writer import persist_chunk


def _built_row(line: int) -> dict:
    prop = MagicMock()
    prop.id = uuid.uuid4()
    return {
        "line": line,
        "id": str(uuid.uuid4()),
        "ref": f"owner{line}@test.com @ 4.6,-74.0",
        "value": (prop, MagicMock(), []),
    }


@pytest.fixture
def uow():
    u = MagicMock()
    u.commit = AsyncMock()
    u.rollback = AsyncMock()
    u.begin_nested = AsyncMock()
    u.release_savepoint = AsyncMock()
    u.rollback_to_savepoint = AsyncMock()
    u.properties = MagicMock()
    return u


def _patch_threadpool(side_effect=None):
    """run_in_threadpool receives a partial; calling it runs the repo method so
    a side_effect can make specific rows fail."""
    async def _run(fn):
        if side_effect is not None:
            return side_effect(fn)
        return fn()

    return patch(
        "app.workers.helpers.persistence.property_writer.run_in_threadpool",
        new=AsyncMock(side_effect=_run),
    )


# ---------------------------------------------------------------------------
# Happy path — one bulk insert, one commit
# ---------------------------------------------------------------------------

async def test_bulk_insert_commits_once_and_reports_every_row(uow):
    rows = [_built_row(2), _built_row(3)]

    with _patch_threadpool():
        inserted, errors = await persist_chunk(rows, uow=uow)

    assert inserted == 2
    assert errors == []
    uow.commit.assert_awaited_once()
    uow.begin_nested.assert_not_awaited()  # no fallback needed


async def test_passes_only_the_orm_tuples_to_the_repo(uow):
    rows = [_built_row(2)]

    with _patch_threadpool():
        await persist_chunk(rows, uow=uow)

    kwargs = uow.properties.bulk_insert.call_args.kwargs
    assert kwargs["properties"] == [rows[0]["value"]]


# ---------------------------------------------------------------------------
# Fallback — bulk fails, rows are retried one by one
# ---------------------------------------------------------------------------

async def test_falls_back_to_row_by_row_when_bulk_insert_fails(uow):
    rows = [_built_row(2), _built_row(3)]
    uow.properties.bulk_insert.side_effect = Exception("constraint violation")

    with _patch_threadpool():
        inserted, errors = await persist_chunk(rows, uow=uow)

    assert inserted == 2
    assert errors == []
    uow.rollback.assert_awaited_once()
    assert uow.begin_nested.await_count == 2


async def test_releases_the_savepoint_on_every_success(uow):
    """Without the release each begin_nested would nest inside the previous one."""
    rows = [_built_row(2), _built_row(3), _built_row(4)]
    uow.properties.bulk_insert.side_effect = Exception("boom")

    with _patch_threadpool():
        await persist_chunk(rows, uow=uow)

    assert uow.release_savepoint.await_count == 3
    uow.rollback_to_savepoint.assert_not_awaited()


async def test_a_failing_row_is_rolled_back_and_reported_with_its_line(uow):
    rows = [_built_row(2), _built_row(3), _built_row(4)]
    uow.properties.bulk_insert.side_effect = Exception("boom")

    def fail_second(fn):
        # the partial for row line=3 carries that row's tuple
        if fn.keywords.get("property") is rows[1]["value"]:
            raise Exception("duplicate key")
        return fn()

    with _patch_threadpool(side_effect=fail_second):
        inserted, errors = await persist_chunk(rows, uow=uow)

    assert inserted == 2
    assert len(errors) == 1
    assert errors[0].line == 3
    assert errors[0].ref == rows[1]["ref"]
    assert "duplicate key" in errors[0].issues[0]
    uow.rollback_to_savepoint.assert_awaited_once()
    assert uow.release_savepoint.await_count == 2


async def test_no_commit_when_every_row_fails(uow):
    rows = [_built_row(2)]
    uow.properties.bulk_insert.side_effect = Exception("boom")

    def fail_all(fn):
        raise Exception("nope")

    with _patch_threadpool(side_effect=fail_all):
        inserted, errors = await persist_chunk(rows, uow=uow)

    assert inserted == 0
    assert len(errors) == 1
    # only the rollback from the failed bulk attempt, never a commit
    uow.commit.assert_not_awaited()
