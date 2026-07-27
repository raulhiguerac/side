import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import PropertyNotFoundError
from app.models.listing import Currency, ListingStatus, ListingType, PropertyCondition, PropertyType, VerificationStatus
from app.schemas.principal import Principal
from app.services.listing.use_cases.property_core.get_property import GetPropertyUseCase
from app.services.shared.schemas.property_detail import PropertyDetailSchema

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
OTHER_USER = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

OWNER_PRINCIPAL = Principal(sub=OWNER_ID)
OTHER_PRINCIPAL = Principal(sub=OTHER_USER)


def _make_mock_prop(status=ListingStatus.active):
    m = MagicMock()
    m.id = PROP_ID
    m.owner_id = OWNER_ID
    m.property_type = PropertyType.apartment
    m.listing_type = ListingType.sale
    m.condition = PropertyCondition.used
    m.status = status
    m.verification_status = VerificationStatus.unverified
    m.price = Decimal("100000.00")
    m.currency = Currency.COP
    m.area_m2 = Decimal("50.00")
    m.bedrooms = 2
    m.bathrooms = Decimal("1.0")
    m.parking_spots = 0
    m.created_at = datetime(2024, 1, 1)
    m.location = None
    m.images = []
    m.admin_fee = None
    m.floor_number = None
    m.total_floors = None
    m.stratum = None
    m.description = None
    m.year_built = None
    return m


CACHED_DETAIL = {
    "id": str(PROP_ID),
    "property_type": "apartment",
    "listing_type": "sale",
    "condition": "used",
    "status": "active",
    "verification_status": "unverified",
    "price": "100000.00",
    "currency": "COP",
    "area_m2": "50.00",
    "bedrooms": 2,
    "bathrooms": "1.0",
    "parking_spots": 0,
    "created_at": "2024-01-01T00:00:00",
    "location": None,
    "images": [],
}


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
    return GetPropertyUseCase(cache=mock_cache, uow=mock_uow)


# ---------------------------------------------------------------------------
# Cache hit
# ---------------------------------------------------------------------------

async def test_returns_cached_result_without_hitting_db(uc, mock_cache, mock_uow):
    mock_cache.get_json.return_value = CACHED_DETAIL

    result = await uc.execute(PROP_ID)

    assert isinstance(result, PropertyDetailSchema)
    assert result.id == PROP_ID
    mock_uow.properties.get_by_id.assert_not_called()


# ---------------------------------------------------------------------------
# Cache miss — found and active
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.get_property.run_in_threadpool")
async def test_fetches_from_db_on_cache_miss_and_caches_result(mock_run, uc, mock_cache):
    prop = _make_mock_prop(ListingStatus.active)
    mock_run.return_value = prop

    result = await uc.execute(PROP_ID)

    assert isinstance(result, PropertyDetailSchema)
    assert result.id == PROP_ID
    mock_cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.get_property.run_in_threadpool")
async def test_raises_not_found_when_property_missing(mock_run, uc):
    mock_run.return_value = None

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(PROP_ID)


# ---------------------------------------------------------------------------
# Visibility — non-owner cannot see non-active property
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.get_property.run_in_threadpool")
async def test_raises_not_found_for_non_owner_accessing_draft(mock_run, uc):
    prop = _make_mock_prop(ListingStatus.draft)
    mock_run.return_value = prop

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(PROP_ID, principal=OTHER_PRINCIPAL)


@patch("app.services.listing.use_cases.property_core.get_property.run_in_threadpool")
async def test_owner_can_see_own_draft_property(mock_run, uc, mock_cache):
    prop = _make_mock_prop(ListingStatus.draft)
    mock_run.return_value = prop

    result = await uc.execute(PROP_ID, principal=OWNER_PRINCIPAL)

    assert isinstance(result, PropertyDetailSchema)
    # Draft properties are not cached
    mock_cache.set_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.get_property.run_in_threadpool")
async def test_survives_cache_write_failure(mock_run, uc, mock_cache):
    prop = _make_mock_prop(ListingStatus.active)
    mock_run.return_value = prop
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute(PROP_ID)

    assert isinstance(result, PropertyDetailSchema)
