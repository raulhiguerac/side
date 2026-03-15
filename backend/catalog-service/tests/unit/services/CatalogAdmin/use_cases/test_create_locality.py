import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions.catalog_admin import LocalityConflictError
from app.models.location import LocalityType
from app.services.catalog_admin.schemas.locality import CreateLocalityRequest, LocalityAdminResponse
from app.services.catalog_admin.use_cases.create_locality import CreateLocalityUseCase

COUNTRY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_DIVISION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
LOCALITY_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

REQUEST = CreateLocalityRequest(
    country_id=COUNTRY_ID,
    admin_division_id=ADMIN_DIVISION_ID,
    code="BOG",
    name="Bogotá",
    locality_type=LocalityType.city,
    latitude=4.7110,
    longitude=-74.0721,
    timezone="America/Bogota",
)


def _make_db_locality():
    m = MagicMock()
    m.id = LOCALITY_ID
    m.country_id = COUNTRY_ID
    m.admin_division_id = ADMIN_DIVISION_ID
    m.code = "BOG"
    m.name = "Bogotá"
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
    return CreateLocalityUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_locality.run_in_threadpool")
async def test_creates_locality_caches_and_invalidates_lists(mock_run, uc, mock_uow, mock_cache):
    locality = _make_db_locality()
    mock_run.return_value = locality

    result = await uc.execute(request=REQUEST)

    assert isinstance(result, LocalityAdminResponse)
    assert result.name == "Bogotá"
    mock_uow.commit.assert_awaited_once()
    mock_uow.refresh.assert_awaited_once_with(locality)
    mock_cache.set_json.assert_awaited_once()
    assert mock_cache.delete.await_count == 2  # by country + by admin_division


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_locality.translate_db_error")
@patch("app.services.catalog_admin.use_cases.create_locality.run_in_threadpool")
async def test_rolls_back_and_raises_on_db_error(mock_run, mock_translate, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_locality()
    mock_uow.commit.side_effect = Exception("unique constraint")
    mock_translate.return_value = LocalityConflictError(field="code", value="BOG")

    with pytest.raises(LocalityConflictError):
        await uc.execute(request=REQUEST)

    mock_uow.rollback.assert_awaited_once()
    mock_cache.set_json.assert_not_awaited()
    mock_cache.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_locality.run_in_threadpool")
async def test_survives_cache_failure(mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_locality()
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute(request=REQUEST)

    assert isinstance(result, LocalityAdminResponse)
    mock_uow.commit.assert_awaited_once()
