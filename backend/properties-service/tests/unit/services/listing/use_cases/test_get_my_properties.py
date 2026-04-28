import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.property import Currency, ListingStatus, ListingType, PropertyType
from app.schemas.principal import Principal
from app.services.listing.use_cases.property_core.get_my_properties import GetMyPropertiesUseCase
from app.services.shared.schemas.property_card import PropertyCardSchema

OWNER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
PROP_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
PRINCIPAL = Principal(sub=OWNER_ID)

CACHED_CARD = {
    "id": str(PROP_ID),
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


def _make_mock_prop():
    m = MagicMock()
    m.id = PROP_ID
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
    return m


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get_json.return_value = None  # cache miss by default
    return cache


@pytest.fixture
def mock_uow():
    return MagicMock()


@pytest.fixture
def uc(mock_cache, mock_uow):
    return GetMyPropertiesUseCase(cache=mock_cache, uow=mock_uow)


# ---------------------------------------------------------------------------
# Cache hit
# ---------------------------------------------------------------------------

async def test_returns_cached_list_without_hitting_db(uc, mock_cache, mock_uow):
    mock_cache.get_json.return_value = [CACHED_CARD]

    result = await uc.execute(PRINCIPAL)

    assert len(result) == 1
    assert isinstance(result[0], PropertyCardSchema)
    mock_uow.properties.get_user_properties.assert_not_called()


# ---------------------------------------------------------------------------
# Cache miss — fetches from DB and caches
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.get_my_properties.run_in_threadpool")
async def test_fetches_from_db_on_cache_miss_and_caches(mock_run, uc, mock_cache):
    prop = _make_mock_prop()
    mock_run.return_value = [prop]

    result = await uc.execute(PRINCIPAL)

    assert len(result) == 1
    assert isinstance(result[0], PropertyCardSchema)
    mock_cache.set_json.assert_awaited_once()


@patch("app.services.listing.use_cases.property_core.get_my_properties.run_in_threadpool")
async def test_returns_empty_list_when_no_properties(mock_run, uc, mock_cache):
    mock_run.return_value = []

    result = await uc.execute(PRINCIPAL)

    assert result == []
    mock_cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.get_my_properties.run_in_threadpool")
async def test_survives_cache_write_failure(mock_run, uc, mock_cache):
    mock_run.return_value = [_make_mock_prop()]
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute(PRINCIPAL)

    assert len(result) == 1
