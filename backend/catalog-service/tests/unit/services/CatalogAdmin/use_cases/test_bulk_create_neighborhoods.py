import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.catalog_admin.schemas.neighborhood import BulkCreateNeighborhoodsResult
from app.services.catalog_admin.use_cases.bulk_create_neighborhoods import BulkCreateNeighborhoodsUseCase

LOCALITY_ID = uuid.UUID("c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33")

RECORDS = [
    {"name": "Chapinero", "code": "001"},
    {"name": "Usaquén", "code": "002"},
    {"name": "Suba", "code": "003"},
]


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.neighborhoods.bulk_insert.return_value = None
    uow.neighborhoods.add.return_value = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.begin_nested = AsyncMock()
    uow.rollback_to_savepoint = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return BulkCreateNeighborhoodsUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Happy path — bulk insert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_create_neighborhoods.run_in_threadpool")
async def test_bulk_insert_happy_path(mock_run, uc, mock_uow):
    mock_run.return_value = None

    result = await uc.execute(locality_id=LOCALITY_ID, records=RECORDS)

    assert result == BulkCreateNeighborhoodsResult(created=3, errors=[])
    mock_uow.commit.assert_awaited_once()
    mock_uow.rollback.assert_not_awaited()
    mock_uow.begin_nested.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_create_neighborhoods.run_in_threadpool")
async def test_returns_empty_result_when_no_records(mock_run, uc, mock_uow):
    mock_run.return_value = None

    result = await uc.execute(locality_id=LOCALITY_ID, records=[])

    assert result == BulkCreateNeighborhoodsResult(created=0, errors=[])
    mock_uow.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Fallback — row-by-row con savepoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_create_neighborhoods.run_in_threadpool")
async def test_fallback_row_by_row_on_bulk_insert_failure(mock_run, uc, mock_uow):
    """Si bulk_insert falla, debe intentar row-by-row con savepoints."""
    mock_run.side_effect = [Exception("constraint violation"), None, None, None]

    result = await uc.execute(locality_id=LOCALITY_ID, records=RECORDS)

    assert result.created == 3
    assert result.errors == []
    mock_uow.rollback.assert_awaited_once()
    assert mock_uow.begin_nested.await_count == 3
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_create_neighborhoods.run_in_threadpool")
async def test_fallback_skips_failing_rows_and_reports_errors(mock_run, uc, mock_uow):
    """En fallback, filas que fallan se reportan en errors pero las demás se insertan."""
    # bulk_insert falla, luego row 1 ok, row 2 falla, row 3 ok
    mock_run.side_effect = [Exception("bulk failed"), None, Exception("duplicate key"), None]

    result = await uc.execute(locality_id=LOCALITY_ID, records=RECORDS)

    assert result.created == 2
    assert len(result.errors) == 1
    assert result.errors[0] == "Usaquén"
    mock_uow.rollback_to_savepoint.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_create_neighborhoods.run_in_threadpool")
async def test_fallback_does_not_commit_when_all_rows_fail(mock_run, uc, mock_uow):
    """Si todas las filas fallan en fallback, no debe hacer commit."""
    mock_run.side_effect = [
        Exception("bulk failed"),
        Exception("row 1 failed"),
        Exception("row 2 failed"),
        Exception("row 3 failed"),
    ]

    result = await uc.execute(locality_id=LOCALITY_ID, records=RECORDS)

    assert result.created == 0
    assert len(result.errors) == 3
    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Normalización de search_name
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.bulk_create_neighborhoods.run_in_threadpool")
async def test_normalizes_search_name(mock_run, uc, mock_uow):
    """search_name debe ser lowercase sin tildes."""
    captured = []

    async def capture(fn):
        result = fn()
        if hasattr(fn, "keywords") and "neighborhoods" in fn.keywords:
            captured.extend(fn.keywords["neighborhoods"])
        return result

    mock_run.side_effect = capture

    await uc.execute(locality_id=LOCALITY_ID, records=[{"name": "Usaquén", "code": "001"}])

    assert len(captured) == 1
    assert captured[0].search_name == "usaquen"
    assert captured[0].name == "Usaquén"
