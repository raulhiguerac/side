import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions.catalog_admin import NeighborhoodConflictError
from app.services.catalog_admin.schemas.neighborhood import CreateNeighborhoodRequest, NeighborhoodAdminResponse
from app.services.catalog_admin.use_cases.create_neighborhood import CreateNeighborhoodUseCase

LOCALITY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
NEIGHBORHOOD_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

REQUEST = CreateNeighborhoodRequest(
    locality_id=LOCALITY_ID,
    code="CHP",
    name="Chapinero",
    latitude=4.6473,
    longitude=-74.0962,
)


def _make_db_neighborhood():
    m = MagicMock()
    m.id = NEIGHBORHOOD_ID
    m.locality_id = LOCALITY_ID
    m.code = "CHP"
    m.name = "Chapinero"
    m.postal_code = None
    m.latitude = 4.6473
    m.longitude = -74.0962
    m.is_active = True
    m.geom = None
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
    return CreateNeighborhoodUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_neighborhood.geom_to_geojson", return_value=None)
@patch("app.services.catalog_admin.use_cases.create_neighborhood.run_in_threadpool")
async def test_creates_neighborhood_caches_and_invalidates_list(mock_run, _mock_geom, uc, mock_uow, mock_cache):
    neighborhood = _make_db_neighborhood()
    mock_run.return_value = neighborhood

    result = await uc.execute(request=REQUEST)

    assert isinstance(result, NeighborhoodAdminResponse)
    assert result.name == "Chapinero"
    mock_uow.commit.assert_awaited_once()
    mock_uow.refresh.assert_awaited_once_with(neighborhood)
    mock_cache.set_json.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()  # invalida cache_key_neighborhoods(locality_id)


@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_neighborhood.geom_to_geojson", return_value=None)
@patch("app.services.catalog_admin.use_cases.create_neighborhood.run_in_threadpool")
async def test_normalizes_search_name(mock_run, _mock_geom, uc, mock_uow, mock_cache):
    neighborhood = _make_db_neighborhood()
    captured = []

    async def capture(fn):
        if hasattr(fn, "keywords") and "neighborhood" in fn.keywords:
            captured.append(fn.keywords["neighborhood"])
        return neighborhood

    mock_run.side_effect = capture

    await uc.execute(request=REQUEST)

    assert len(captured) == 1
    assert captured[0].search_name == "chapinero"


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_neighborhood.translate_db_error")
@patch("app.services.catalog_admin.use_cases.create_neighborhood.run_in_threadpool")
async def test_rolls_back_and_raises_on_db_error(mock_run, mock_translate, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_neighborhood()
    mock_uow.commit.side_effect = Exception("unique constraint")
    mock_translate.return_value = NeighborhoodConflictError(field="code", value="CHP")

    with pytest.raises(NeighborhoodConflictError):
        await uc.execute(request=REQUEST)

    mock_uow.rollback.assert_awaited_once()
    mock_cache.set_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_neighborhood.geom_to_geojson", return_value=None)
@patch("app.services.catalog_admin.use_cases.create_neighborhood.run_in_threadpool")
async def test_survives_cache_failure(mock_run, _mock_geom, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_neighborhood()
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute(request=REQUEST)

    assert isinstance(result, NeighborhoodAdminResponse)
    mock_uow.commit.assert_awaited_once()
