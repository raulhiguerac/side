import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import (
    InvalidStatusTransitionError,
    PropertyForbiddenError,
    PropertyNotFoundError,
    SetVisibilityError,
)
from app.models.listing import ListingStatus
from app.schemas.principal import Principal
from app.services.listing.use_cases.property_core.set_property_visibility import SetPropertyVisibilityUseCase

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
PRINCIPAL = Principal(sub=OWNER_ID)


def _make_mock_prop(status: ListingStatus):
    m = MagicMock()
    m.id = PROP_ID
    m.owner_id = OWNER_ID
    m.status = status
    return m


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
    return SetPropertyVisibilityUseCase(cache=mock_cache, uow=mock_uow)


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.set_property_visibility.get_owned_property", new_callable=AsyncMock)
async def test_transitions_draft_to_active(mock_get_prop, uc, mock_uow, mock_cache):
    prop = _make_mock_prop(ListingStatus.draft)
    mock_get_prop.return_value = prop

    await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    assert prop.status == ListingStatus.active
    mock_uow.commit.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


@patch("app.services.listing.use_cases.property_core.set_property_visibility.get_owned_property", new_callable=AsyncMock)
async def test_transitions_active_to_draft(mock_get_prop, uc, mock_uow, mock_cache):
    prop = _make_mock_prop(ListingStatus.active)
    mock_get_prop.return_value = prop

    await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    assert prop.status == ListingStatus.draft
    mock_uow.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Invalid transition
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.set_property_visibility.get_owned_property", new_callable=AsyncMock)
async def test_raises_invalid_transition_for_sold_property(mock_get_prop, uc, mock_uow):
    mock_get_prop.return_value = _make_mock_prop(ListingStatus.sold)

    with pytest.raises(InvalidStatusTransitionError):
        await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Not found / forbidden — delegated to guard
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.set_property_visibility.get_owned_property", new_callable=AsyncMock)
async def test_raises_not_found(mock_get_prop, uc, mock_uow):
    mock_get_prop.side_effect = PropertyNotFoundError(property_id=PROP_ID)

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    mock_uow.commit.assert_not_awaited()


@patch("app.services.listing.use_cases.property_core.set_property_visibility.get_owned_property", new_callable=AsyncMock)
async def test_raises_forbidden(mock_get_prop, uc, mock_uow):
    mock_get_prop.side_effect = PropertyForbiddenError(property_id=PROP_ID)

    with pytest.raises(PropertyForbiddenError):
        await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.set_property_visibility.get_owned_property", new_callable=AsyncMock)
async def test_rolls_back_and_raises_set_visibility_error_on_commit_failure(mock_get_prop, uc, mock_uow):
    mock_get_prop.return_value = _make_mock_prop(ListingStatus.draft)
    mock_uow.commit.side_effect = Exception("db error")

    with pytest.raises(SetVisibilityError):
        await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    mock_uow.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.set_property_visibility.get_owned_property", new_callable=AsyncMock)
async def test_survives_cache_delete_failure(mock_get_prop, uc, mock_uow, mock_cache):
    mock_get_prop.return_value = _make_mock_prop(ListingStatus.draft)
    mock_cache.delete.side_effect = Exception("Redis down")

    await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    mock_uow.commit.assert_awaited_once()
