import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.services.geo_resolution.use_cases.resolve_poi import ResolvePoiUseCase, STALE_THRESHOLD_DAYS
from app.models.location import FetchZone

LOCALITY_ID = uuid.UUID("86f1f356-e83a-47f4-b50b-0cf7bb5d9ac5")
NEIGHBORHOOD_ID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
LAT = 4.6097
LON = -74.0817
H3_INDEX = "89b4e30d7ffffff"

MOCK_POIS = [MagicMock(), MagicMock()]


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.fetch_zones.get_by_h3_index.return_value = None
    uow.pois.add_many.return_value = None
    uow.fetch_zones.add.return_value = None
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get.return_value = None
    cache.set_nx.return_value = True
    cache.set.return_value = None
    cache.delete.return_value = None
    return cache


@pytest.fixture
def mock_poi_provider():
    provider = AsyncMock()
    provider.get_pois_by_bbox.return_value = MOCK_POIS
    return provider


@pytest.fixture
def uc(mock_uow, mock_cache, mock_poi_provider):
    return ResolvePoiUseCase(
        uow=mock_uow,
        cache_client=mock_cache,
        poi_provider=mock_poi_provider,
    )


# ---------------------------------------------------------------------------
# Early exits
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_exits_early_when_fetch_zone_cached(mock_h3, uc, mock_cache, mock_poi_provider):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    mock_cache.get.return_value = "1"

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    mock_poi_provider.get_pois_by_bbox.assert_not_awaited()
    mock_cache.set_nx.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_exits_early_when_lock_not_acquired(mock_h3, uc, mock_cache, mock_poi_provider):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    mock_cache.get.return_value = None
    mock_cache.set_nx.return_value = False

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    mock_poi_provider.get_pois_by_bbox.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.run_in_threadpool")
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_exits_early_when_zone_is_fresh(mock_h3, mock_run, uc, mock_cache, mock_uow, mock_poi_provider):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    fresh_zone = MagicMock(spec=FetchZone)
    fresh_zone.fetched_at = datetime.now(timezone.utc) - timedelta(days=1)
    mock_run.return_value = fresh_zone

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    mock_poi_provider.get_pois_by_bbox.assert_not_awaited()
    mock_cache.set.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# Stale zone
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.run_in_threadpool")
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_marks_stale_and_returns_when_zone_expired(
    mock_h3, mock_run, uc, mock_cache, mock_uow, mock_poi_provider
):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    stale_zone = MagicMock(spec=FetchZone)
    stale_zone.fetched_at = datetime.now(timezone.utc) - timedelta(days=STALE_THRESHOLD_DAYS + 1)
    mock_run.return_value = stale_zone

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    assert stale_zone.is_stale is True
    mock_uow.commit.assert_awaited_once()
    mock_poi_provider.get_pois_by_bbox.assert_not_awaited()
    mock_cache.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# Happy path — fetch from provider
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.run_in_threadpool")
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_fetches_pois_and_persists_when_no_zone(
    mock_h3, mock_run, uc, mock_cache, mock_uow, mock_poi_provider
):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    mock_h3.cell_to_boundary.return_value = [
        (4.60, -74.09), (4.61, -74.09), (4.61, -74.07), (4.60, -74.07)
    ]
    mock_run.return_value = None  # no FetchZone exists

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    mock_poi_provider.get_pois_by_bbox.assert_awaited_once()
    # run_in_threadpool llamado para add_many y fetch_zones.add
    assert mock_run.call_count == 3  # get_by_h3_index + add_many + fetch_zones.add
    mock_uow.commit.assert_awaited_once()
    mock_cache.set.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.run_in_threadpool")
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_fetch_zone_saved_with_correct_poi_count(
    mock_h3, mock_run, uc, mock_cache, mock_uow, mock_poi_provider
):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    mock_h3.cell_to_boundary.return_value = [
        (4.60, -74.09), (4.61, -74.09), (4.61, -74.07), (4.60, -74.07)
    ]
    mock_run.return_value = None

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    # Extraer el FetchZone pasado al add de fetch_zones
    add_call = mock_run.call_args_list[2]
    partial_fn = add_call[0][0]
    fetch_zone = partial_fn.keywords["fetch_zone"]

    assert fetch_zone.h3_index == H3_INDEX
    assert fetch_zone.locality_id == LOCALITY_ID
    assert fetch_zone.poi_count == len(MOCK_POIS)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.run_in_threadpool")
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_rollback_on_provider_error(
    mock_h3, mock_run, uc, mock_cache, mock_uow, mock_poi_provider
):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    mock_h3.cell_to_boundary.return_value = [
        (4.60, -74.09), (4.61, -74.09), (4.61, -74.07), (4.60, -74.07)
    ]
    mock_run.return_value = None
    mock_poi_provider.get_pois_by_bbox.side_effect = Exception("Overpass timeout")

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    mock_uow.rollback.assert_awaited_once()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.run_in_threadpool")
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_lock_released_on_error(
    mock_h3, mock_run, uc, mock_cache, mock_uow, mock_poi_provider
):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    mock_h3.cell_to_boundary.return_value = [
        (4.60, -74.09), (4.61, -74.09), (4.61, -74.07), (4.60, -74.07)
    ]
    mock_run.return_value = None
    mock_poi_provider.get_pois_by_bbox.side_effect = Exception("Overpass timeout")

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    mock_cache.delete.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.run_in_threadpool")
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_lock_released_on_success(
    mock_h3, mock_run, uc, mock_cache, mock_uow, mock_poi_provider
):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    mock_h3.cell_to_boundary.return_value = [
        (4.60, -74.09), (4.61, -74.09), (4.61, -74.07), (4.60, -74.07)
    ]
    mock_run.return_value = None

    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    mock_cache.delete.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.geo_resolution.use_cases.resolve_poi.run_in_threadpool")
@patch("app.services.geo_resolution.use_cases.resolve_poi.h3")
async def test_cache_set_failure_does_not_raise(
    mock_h3, mock_run, uc, mock_cache, mock_uow, mock_poi_provider
):
    mock_h3.latlng_to_cell.return_value = H3_INDEX
    mock_h3.cell_to_boundary.return_value = [
        (4.60, -74.09), (4.61, -74.09), (4.61, -74.07), (4.60, -74.07)
    ]
    mock_run.return_value = None
    mock_cache.set.side_effect = Exception("Redis down")

    # No debe explotar
    await uc.execute(lat=LAT, lon=LON, locality_id=LOCALITY_ID, neighborhood_id=NEIGHBORHOOD_ID)

    mock_uow.commit.assert_awaited_once()
