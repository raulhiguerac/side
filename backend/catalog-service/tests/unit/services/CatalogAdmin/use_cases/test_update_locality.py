import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions.catalog_admin import LocalityAdminNotFoundError, LocalityConflictError
from app.models.location import LocalityType
from app.services.catalog_admin.schemas.locality import UpdateLocalityRequest, LocalityAdminResponse
from app.services.catalog_admin.use_cases.update_locality import UpdateLocalityUseCase

COUNTRY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_DIVISION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
LOCALITY_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

REQUEST = UpdateLocalityRequest(name="Bogotá D.C.", is_active=True)


def _make_db_locality():
    m = MagicMock()
    m.id = LOCALITY_ID
    m.country_id = COUNTRY_ID
    m.admin_division_id = ADMIN_DIVISION_ID
    m.code = "BOG"
    m.name = "Bogotá D.C."
    m.local_name = None
    m.locality_type = LocalityType.city
    m.latitude = 4.7110
    m.longitude = -74.0721
    m.timezone = "America/Bogota"
    m.is_active = True
    m.is_capital = False
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.refresh = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return UpdateLocalityUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_locality.run_in_threadpool")
async def test_updates_locality_caches_and_invalidates_lists(mock_run, uc, mock_uow, mock_cache):
    locality = _make_db_locality()
    mock_run.return_value = locality

    result = await uc.execute(locality_id=LOCALITY_ID, request=REQUEST)

    assert isinstance(result, LocalityAdminResponse)
    mock_uow.commit.assert_awaited_once()
    mock_uow.refresh.assert_awaited_once_with(locality)
    mock_cache.set_json.assert_awaited_once()
    assert mock_cache.delete.await_count == 2  # by country + by admin_division


@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_locality.run_in_threadpool")
async def test_normalizes_search_name_when_name_updated(mock_run, uc, mock_uow, mock_cache):
    locality = _make_db_locality()
    mock_run.return_value = locality

    await uc.execute(locality_id=LOCALITY_ID, request=UpdateLocalityRequest(name="Usaquén"))

    assert locality.search_name == "usaquen"


@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_locality.run_in_threadpool")
async def test_does_not_touch_search_name_when_name_not_updated(mock_run, uc, mock_uow, mock_cache):
    locality = _make_db_locality()
    mock_run.return_value = locality

    await uc.execute(locality_id=LOCALITY_ID, request=UpdateLocalityRequest(is_active=False))

    assert not hasattr(locality, "search_name") or locality.search_name != "bogota d.c."


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_locality.run_in_threadpool")
async def test_raises_not_found_when_locality_missing(mock_run, uc, mock_uow):
    mock_run.return_value = None

    with pytest.raises(LocalityAdminNotFoundError):
        await uc.execute(locality_id=LOCALITY_ID, request=REQUEST)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_locality.translate_db_error")
@patch("app.services.catalog_admin.use_cases.update_locality.run_in_threadpool")
async def test_rolls_back_and_raises_on_db_error(mock_run, mock_translate, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_locality()
    mock_uow.commit.side_effect = Exception("unique constraint")
    mock_translate.return_value = LocalityConflictError(field="code", value="BOG")

    with pytest.raises(LocalityConflictError):
        await uc.execute(locality_id=LOCALITY_ID, request=REQUEST)

    mock_uow.rollback.assert_awaited_once()
    mock_cache.set_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_locality.run_in_threadpool")
async def test_survives_cache_failure(mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_locality()
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute(locality_id=LOCALITY_ID, request=REQUEST)

    assert isinstance(result, LocalityAdminResponse)
    mock_uow.commit.assert_awaited_once()
