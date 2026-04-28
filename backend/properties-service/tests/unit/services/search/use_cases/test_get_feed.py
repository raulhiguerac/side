import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.property import Currency, ListingStatus, ListingType, PropertyType
from app.services.search.schemas.feed_schemas import FeedCursor, FeedFilters, FeedPreferences
from app.services.search.use_cases.get_feed import GetFeedUseCase
from app.services.shared.schemas.property_card import PropertyCardSchema

from datetime import datetime


def _make_card(prop_id: uuid.UUID | None = None) -> PropertyCardSchema:
    return PropertyCardSchema(
        id=prop_id or uuid.uuid4(),
        property_type=PropertyType.apartment,
        listing_type=ListingType.sale,
        status=ListingStatus.active,
        price=Decimal("100000.00"),
        currency=Currency.COP,
        area_m2=Decimal("50.00"),
        bedrooms=2,
        bathrooms=Decimal("1.0"),
        parking_spots=0,
    )


@pytest.fixture
def mock_uow():
    return MagicMock()


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return GetFeedUseCase(uow=mock_uow, cache=mock_cache)


# ---------------------------------------------------------------------------
# Cursor past max — short circuit
# ---------------------------------------------------------------------------

async def test_returns_empty_list_when_cursor_past_max_results(uc):
    from app.core.config.settings import settings
    cursor = FeedCursor(
        created_at=datetime(2024, 1, 1),
        id=uuid.uuid4(),
        position=settings.FEED_MAX_RESULTS,
    )

    result = await uc.execute(preferences=None, filters=None, cursor=cursor)

    assert result == []


# ---------------------------------------------------------------------------
# No ads — returns organic directly
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed.get_organic", new_callable=AsyncMock)
@patch("app.services.search.use_cases.get_feed.get_ads", new_callable=AsyncMock)
async def test_returns_organic_only_when_no_ads(mock_ads, mock_organic, uc):
    organic = [_make_card() for _ in range(5)]
    mock_ads.return_value = []
    mock_organic.return_value = organic

    result = await uc.execute(preferences=None, filters=None, cursor=None)

    assert result == organic
    mock_ads.assert_awaited_once()
    mock_organic.assert_awaited_once()


# ---------------------------------------------------------------------------
# Ads injection
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed.get_organic", new_callable=AsyncMock)
@patch("app.services.search.use_cases.get_feed.get_ads", new_callable=AsyncMock)
async def test_injects_ads_at_correct_interval(mock_ads, mock_organic, uc):
    from app.core.config.settings import settings
    ad = _make_card()
    organic = [_make_card() for _ in range(settings.FEED_AD_INTERVAL)]

    mock_ads.return_value = [ad]
    mock_organic.return_value = organic

    result = await uc.execute(preferences=None, filters=None, cursor=None)

    # After FEED_AD_INTERVAL organic cards, 1 ad should be injected
    assert len(result) == settings.FEED_AD_INTERVAL + 1
    assert result[-1] == ad


# ---------------------------------------------------------------------------
# inject_ads static method
# ---------------------------------------------------------------------------

def test_inject_ads_places_ad_every_interval():
    ad_id = uuid.uuid4()
    ad = _make_card(ad_id)
    organic = [_make_card() for _ in range(10)]

    result = GetFeedUseCase._inject_ads(
        organic=organic,
        ads=[ad],
        ad_interval=5,
        ad_start=0,
    )

    # 10 organic + 2 ads (after position 5 and 10)
    assert len(result) == 12
    assert result[5] == ad
    assert result[11] == ad


def test_inject_ads_wraps_around_ad_list():
    ad1 = _make_card()
    ad2 = _make_card()
    organic = [_make_card() for _ in range(10)]

    result = GetFeedUseCase._inject_ads(
        organic=organic,
        ads=[ad1, ad2],
        ad_interval=5,
        ad_start=0,
    )

    assert result[5] == ad1   # first ad slot
    assert result[11] == ad2  # second ad slot


def test_inject_ads_respects_ad_start_offset():
    ad1 = _make_card()
    ad2 = _make_card()
    organic = [_make_card() for _ in range(5)]

    result = GetFeedUseCase._inject_ads(
        organic=organic,
        ads=[ad1, ad2],
        ad_interval=5,
        ad_start=1,  # start at second ad
    )

    assert result[5] == ad2


# ---------------------------------------------------------------------------
# Preferences passed through to get_organic
# ---------------------------------------------------------------------------

@patch("app.services.search.use_cases.get_feed.get_organic", new_callable=AsyncMock)
@patch("app.services.search.use_cases.get_feed.get_ads", new_callable=AsyncMock)
async def test_passes_preferences_and_filters_to_helpers(mock_ads, mock_organic, uc):
    mock_ads.return_value = []
    mock_organic.return_value = []
    preferences = FeedPreferences(
        city_ids=[uuid.uuid4()],
        neighborhood_ids=[],
        property_types=[PropertyType.apartment],
    )
    filters = FeedFilters(min_price=Decimal("50000.00"))

    await uc.execute(preferences=preferences, filters=filters, cursor=None)

    call_kwargs = mock_organic.call_args.kwargs
    assert call_kwargs["preferences"] == preferences
    assert call_kwargs["filters"] == filters
