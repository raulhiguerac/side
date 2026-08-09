import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.core.exceptions.listing import (
    DuplicateActivePromotionError,
    PropertyNotFoundError,
    PropertyNotReadyForPromotionError,
)
from app.models.listing import ListingStatus
from app.schemas.principal import Principal
from app.services.admin.schemas.admin_schemas import CreatePromotionRequest
from app.services.admin.use_cases.promotions.create import CreatePromotionUseCase
from app.services.shared.helpers.cache_keys import feed_ads_by_city, feed_ads_global

MODULE = "app.services.admin.use_cases.promotions.create"

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
CITY_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
ADMIN = Principal(sub=uuid.UUID("11111111-1111-1111-1111-111111111111"))


def _make_prop(status: ListingStatus = ListingStatus.active):
    return SimpleNamespace(
        id = PROP_ID,
        owner_id = OWNER_ID,
        status = status,
        location = SimpleNamespace(city_id=CITY_ID),
    )


def _request(days: int = 7, priority: int = 1) -> CreatePromotionRequest:
    return CreatePromotionRequest(
        property_id = PROP_ID,
        promoted_days = days,
        priority = priority,
    )


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return CreatePromotionUseCase(uow=mock_uow, cache=mock_cache)


# ---------------------------------------------------------------------------
# Duración: el tope también es del backend
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("days", [1, 30, 60])
def test_accepts_duration_within_bounds(days):
    assert _request(days=days).promoted_days == days


@pytest.mark.parametrize("days", [0, -1, 61, 3000])
def test_rejects_duration_out_of_bounds(days):
    """El tope existía solo en el front hasta el 2026-08-09: por API se podían
    pedir 3.000 días."""
    with pytest.raises(ValidationError):
        _request(days=days)


# ---------------------------------------------------------------------------
# Las dos reglas que el listado admin expone como filtros
# ---------------------------------------------------------------------------

@patch(f"{MODULE}.run_in_threadpool")
async def test_rejects_property_not_active(mock_run, uc, mock_uow):
    mock_run.return_value = _make_prop(ListingStatus.draft)

    with pytest.raises(PropertyNotReadyForPromotionError):
        await uc.execute(principal=ADMIN, promotion_request=_request())

    mock_uow.commit.assert_not_awaited()


@patch(f"{MODULE}.run_in_threadpool")
async def test_rejects_second_active_promotion(mock_run, uc, mock_uow):
    mock_run.side_effect = [_make_prop(), MagicMock()]  # property, promoción vigente

    with pytest.raises(DuplicateActivePromotionError):
        await uc.execute(principal=ADMIN, promotion_request=_request())

    mock_uow.commit.assert_not_awaited()


@patch(f"{MODULE}.run_in_threadpool")
async def test_raises_not_found_when_property_missing(mock_run, uc):
    mock_run.return_value = None

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(principal=ADMIN, promotion_request=_request())


# ---------------------------------------------------------------------------
# Efectos
# ---------------------------------------------------------------------------

@patch(f"{MODULE}.run_in_threadpool")
async def test_creates_promotion_and_invalidates_feed_ads(mock_run, uc, mock_uow, mock_cache):
    mock_run.side_effect = [_make_prop(), None, None]  # property, sin promo previa, add

    await uc.execute(principal=ADMIN, promotion_request=_request(days=7, priority=4))

    mock_uow.commit.assert_awaited_once()
    deleted = mock_cache.delete.call_args.kwargs["key"]
    assert feed_ads_global() in deleted
    assert feed_ads_by_city(CITY_ID) in deleted


@patch(f"{MODULE}.run_in_threadpool")
async def test_promotion_ends_after_it_starts(mock_run, uc, mock_uow):
    mock_run.side_effect = [_make_prop(), None, None]

    await uc.execute(principal=ADMIN, promotion_request=_request(days=15, priority=2))

    # El `partial` del `add` lleva la promoción construida por el UC.
    add_call = mock_run.call_args_list[2].args[0]
    promotion = add_call.keywords["promotion"]
    assert (promotion.ends_at - promotion.starts_at).days == 15
    assert promotion.priority == 2
    assert promotion.is_active is True
