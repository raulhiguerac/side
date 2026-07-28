import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.listing import Currency, ListingStatus, ListingType, PropertyType
from app.services.search.use_cases.get_feed_map import GetFeedMapUseCase
from app.services.shared.schemas.property_card import PropertyCardSchema

H3_CELL_1 = "8fb5a30a2dfffff"
H3_CELL_2 = "8fb5a30a3dfffff"


def _make_mock_prop(h3_r9: str = H3_CELL_1) -> MagicMock:
    m = MagicMock()
    m.id = uuid.uuid4()
    m.property_type = PropertyType.apartment
    m.listing_type = ListingType.sale
    m.status = ListingStatus.active
    m.price = Decimal("100000.00")
    m.currency = Currency.COP
    m.area_m2 = Decimal("50.00")
    m.bedrooms = 2
    m.bathrooms = Decimal("1.0")
    m.parking_spots = 0
    m.location = None
    m.images = []
    m.h3_r9 = h3_r9
    m.h3_r7 = H3_CELL_1
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return GetFeedMapUseCase(uow=mock_uow, cache=mock_cache)


def _make_bbox():
    """Returns a MagicMock bbox that avoids calling real h3 in to_polygon()."""
    bbox = MagicMock()
    bbox.to_polygon.return_value = MagicMock()
    return bbox


# ---------------------------------------------------------------------------
# Empty h3 indexes — short circuit
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed_map.h3.h3shape_to_cells_experimental", return_value=[])
async def test_returns_empty_list_when_no_h3_cells_in_bbox(_mock_h3, uc):
    result = await uc.execute(bbox=_make_bbox())

    assert result == []


# ---------------------------------------------------------------------------
# All cells cached
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed_map.h3.h3shape_to_cells_experimental", return_value=[H3_CELL_1, H3_CELL_2])
async def test_returns_cached_results_without_db_hit(_mock_h3, uc, mock_cache, mock_uow):
    cached_card = {
        "id": str(uuid.uuid4()),
        "property_type": "apartment",
        "listing_type": "sale",
        "status": "active",
        "price": "100000.00",
        "currency": "COP",
        "area_m2": "50.00",
        "bedrooms": 2,
        "bathrooms": "1.0",
        "parking_spots": 0,
        "location": None,
        "images": [],
    }
    mock_cache.mget_json.return_value = [[cached_card], [cached_card]]

    result = await uc.execute(bbox=_make_bbox())

    assert len(result) == 2
    assert all(isinstance(p, PropertyCardSchema) for p in result)
    mock_uow.properties.get_by_bbox.assert_not_called()


# ---------------------------------------------------------------------------
# Cache miss — fetches from DB and caches by cell
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed_map.h3.h3shape_to_cells_experimental", return_value=[H3_CELL_1])
@patch("app.services.search.use_cases.get_feed_map.run_in_threadpool")
async def test_fetches_from_db_on_cache_miss_and_caches_by_h3_cell(mock_run, _mock_h3, uc, mock_cache):
    prop = _make_mock_prop(h3_r9=H3_CELL_1)
    mock_run.return_value = [prop]
    mock_cache.mget_json.return_value = [None]  # cache miss

    result = await uc.execute(bbox=_make_bbox())

    assert len(result) == 1
    assert isinstance(result[0], PropertyCardSchema)
    mock_cache.mset_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# Partial cache — cached + missing merged
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed_map.h3.h3shape_to_cells_experimental", return_value=[H3_CELL_1, H3_CELL_2])
@patch("app.services.search.use_cases.get_feed_map.run_in_threadpool")
async def test_merges_cached_and_fresh_results(mock_run, _mock_h3, uc, mock_cache):
    cached_card = {
        "id": str(uuid.uuid4()),
        "property_type": "apartment",
        "listing_type": "sale",
        "status": "active",
        "price": "100000.00",
        "currency": "COP",
        "area_m2": "50.00",
        "bedrooms": 2,
        "bathrooms": "1.0",
        "parking_spots": 0,
        "location": None,
        "images": [],
    }
    # CELL_1 is cached, CELL_2 is missing
    mock_cache.mget_json.return_value = [[cached_card], None]

    fresh_prop = _make_mock_prop(h3_r9=H3_CELL_2)
    mock_run.return_value = [fresh_prop]

    result = await uc.execute(bbox=_make_bbox())

    assert len(result) == 2  # 1 cached + 1 fresh
    mock_run.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache error falls back to DB for all cells
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed_map.h3.h3shape_to_cells_experimental", return_value=[H3_CELL_1])
@patch("app.services.search.use_cases.get_feed_map.run_in_threadpool")
async def test_falls_back_to_db_when_cache_raises(mock_run, _mock_h3, uc, mock_cache):
    mock_cache.mget_json.side_effect = Exception("Redis down")
    prop = _make_mock_prop(h3_r9=H3_CELL_1)
    mock_run.return_value = [prop]

    result = await uc.execute(bbox=_make_bbox())

    assert len(result) == 1
    mock_run.assert_awaited_once()


# ---------------------------------------------------------------------------
# mset_json failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed_map.h3.h3shape_to_cells_experimental", return_value=[H3_CELL_1])
@patch("app.services.search.use_cases.get_feed_map.run_in_threadpool")
async def test_survives_cache_write_failure(mock_run, _mock_h3, uc, mock_cache):
    mock_cache.mget_json.return_value = [None]
    mock_run.return_value = [_make_mock_prop(h3_r9=H3_CELL_1)]
    mock_cache.mset_json.side_effect = Exception("Redis down")

    result = await uc.execute(bbox=_make_bbox())

    assert len(result) == 1
