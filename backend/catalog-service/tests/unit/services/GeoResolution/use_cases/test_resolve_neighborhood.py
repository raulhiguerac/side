import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.geo_resolution.use_cases.resolve_neighborhood import ResolveNeighborhoodUseCase
from app.services.geo_resolution.schemas.neighborhood import NeighborhoodInfo, ResolvedNeighborhood
from app.core.exceptions.geo_resolution import NeighborhoodResolutionError

LOCALITY_ID = uuid.UUID("86f1f356-e83a-47f4-b50b-0cf7bb5d9ac5")
NEIGHBORHOOD_ID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
LAT = 4.6097
LON = -74.0817

NEIGHBORHOOD_INFO = NeighborhoodInfo(
    id=NEIGHBORHOOD_ID,
    locality_id=LOCALITY_ID,
    name="Chapinero",
    h3_cells=["89b4e30d7ffffff"],
)

GEOCODE_RESULT = MagicMock()
GEOCODE_RESULT.latitude = LAT
GEOCODE_RESULT.longitude = LON


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.georef.get_neighborhood_by_coordinates.return_value = MagicMock(
        **NEIGHBORHOOD_INFO.model_dump()
    )
    return uow


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get_json.return_value = None
    return cache


@pytest.fixture
def mock_georef():
    georef = AsyncMock()
    georef.forward_geocode.return_value = GEOCODE_RESULT
    return georef


@pytest.fixture
def uc(mock_uow, mock_cache, mock_georef):
    return ResolveNeighborhoodUseCase(
        uow=mock_uow,
        cache_client=mock_cache,
        georef=mock_georef,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_neighborhood.run_in_threadpool")
async def test_returns_resolved_neighborhood_on_cache_miss(
    mock_run, uc, mock_uow, mock_cache, mock_georef
):
    mock_run.return_value = SimpleNamespace(**NEIGHBORHOOD_INFO.model_dump())

    result = await uc.execute(query="Calle 72", locality_id=LOCALITY_ID)

    assert isinstance(result, ResolvedNeighborhood)
    assert result.latitude == LAT
    assert result.longitude == LON
    mock_georef.forward_geocode.assert_awaited_once_with(query="Calle 72")
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_neighborhood.run_in_threadpool")
async def test_uses_cached_coordinates_skips_geocoding(
    mock_run, uc, mock_uow, mock_cache, mock_georef
):
    mock_cache.get_json.return_value = {"lat": LAT, "lon": LON}
    mock_run.return_value = SimpleNamespace(**NEIGHBORHOOD_INFO.model_dump())

    result = await uc.execute(query="Calle 72", locality_id=LOCALITY_ID)

    assert result.latitude == LAT
    assert result.longitude == LON
    mock_georef.forward_geocode.assert_not_awaited()
    mock_cache.set_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache resilience
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_neighborhood.run_in_threadpool")
async def test_survives_cache_get_failure_falls_back_to_geocoding(
    mock_run, uc, mock_uow, mock_cache, mock_georef
):
    mock_cache.get_json.side_effect = Exception("Redis down")
    mock_run.return_value = SimpleNamespace(**NEIGHBORHOOD_INFO.model_dump())

    result = await uc.execute(query="Calle 72", locality_id=LOCALITY_ID)

    assert result.latitude == LAT
    mock_georef.forward_geocode.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_neighborhood.run_in_threadpool")
async def test_survives_cache_set_failure_still_returns_result(
    mock_run, uc, mock_uow, mock_cache, mock_georef
):
    mock_cache.set_json.side_effect = Exception("Redis down")
    mock_run.return_value = SimpleNamespace(**NEIGHBORHOOD_INFO.model_dump())

    result = await uc.execute(query="Calle 72", locality_id=LOCALITY_ID)

    assert result.latitude == LAT
    mock_georef.forward_geocode.assert_awaited_once()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_neighborhood.run_in_threadpool")
async def test_raises_when_no_neighborhood_found(
    mock_run, uc, mock_uow, mock_cache, mock_georef
):
    mock_run.return_value = None

    with pytest.raises(NeighborhoodResolutionError):
        await uc.execute(query="Calle 72", locality_id=LOCALITY_ID)

    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_neighborhood.run_in_threadpool")
async def test_cache_not_set_when_neighborhood_not_found(
    mock_run, uc, mock_uow, mock_cache, mock_georef
):
    """Coordenadas se cachean igual — el miss de neighborhood no las invalida."""
    mock_run.return_value = None

    with pytest.raises(NeighborhoodResolutionError):
        await uc.execute(query="Calle 72", locality_id=LOCALITY_ID)

    mock_cache.set_json.assert_awaited_once()
