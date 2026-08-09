import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import (
    InvalidStatusTransitionError,
    PropertyNotFoundError,
    SetVisibilityError,
)
from app.models.listing import ListingStatus
from app.schemas.principal import Principal
from app.services.admin.use_cases.moderation.set_status import SetPropertyStatusUseCase
from app.services.shared.helpers.cache_keys import (
    cache_property,
    client_properties,
    feed_ads_by_city,
    feed_ads_global,
    map_h3_cell,
)

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
ADMIN_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN = Principal(sub=ADMIN_ID)

H3_R9 = "8fb5a30a2dfffff"
H3_R7 = "87b5a30a2ffffff"


CITY_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


def _make_mock_prop(status: ListingStatus):
    m = MagicMock()
    m.id = PROP_ID
    m.owner_id = OWNER_ID
    m.status = status
    m.h3_r9 = H3_R9
    m.h3_r7 = H3_R7
    m.location = MagicMock(city_id=CITY_ID)
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
    return SetPropertyStatusUseCase(uow=mock_uow, cache=mock_cache)


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_transitions_draft_to_active(mock_run, uc, mock_uow, mock_cache):
    prop = _make_mock_prop(ListingStatus.draft)
    mock_run.return_value = prop

    await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.active)

    assert prop.status == ListingStatus.active
    assert prop.updated_by == ADMIN_ID
    mock_uow.commit.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_transitions_active_to_sold(mock_run, uc, mock_uow, mock_cache):
    prop = _make_mock_prop(ListingStatus.active)
    mock_run.return_value = prop

    await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.sold)

    assert prop.status == ListingStatus.sold
    mock_uow.commit.assert_awaited_once()


@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_transitions_active_to_inactive(mock_run, uc, mock_uow):
    prop = _make_mock_prop(ListingStatus.active)
    mock_run.return_value = prop

    await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.inactive)

    assert prop.status == ListingStatus.inactive


@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_transitions_sold_to_inactive(mock_run, uc, mock_uow):
    prop = _make_mock_prop(ListingStatus.sold)
    mock_run.return_value = prop

    await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.inactive)

    assert prop.status == ListingStatus.inactive


# ---------------------------------------------------------------------------
# Cache includes H3 keys
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_invalidates_property_user_and_h3_cache_keys(mock_run, uc, mock_cache):
    prop = _make_mock_prop(ListingStatus.draft)
    mock_run.return_value = prop

    await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.active)

    call_args = mock_cache.delete.call_args
    deleted_keys = call_args.kwargs["key"]
    assert cache_property(property_id=PROP_ID) in deleted_keys
    assert client_properties(user_id=OWNER_ID) in deleted_keys
    assert map_h3_cell(H3_R9) in deleted_keys
    assert map_h3_cell(H3_R7) in deleted_keys


# ---------------------------------------------------------------------------
# Invalid transition
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_raises_invalid_transition(mock_run, uc, mock_uow):
    mock_run.return_value = _make_mock_prop(ListingStatus.sold)

    with pytest.raises(InvalidStatusTransitionError):
        await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.active)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_raises_not_found_when_property_missing(mock_run, uc, mock_uow):
    mock_run.return_value = None

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.active)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_rolls_back_and_raises_set_visibility_error_on_commit_failure(mock_run, uc, mock_uow):
    mock_run.return_value = _make_mock_prop(ListingStatus.draft)
    mock_uow.commit.side_effect = Exception("db error")

    with pytest.raises(SetVisibilityError):
        await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.active)

    mock_uow.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_survives_cache_delete_failure(mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_mock_prop(ListingStatus.draft)
    mock_cache.delete.side_effect = Exception("Redis down")

    await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.active)

    mock_uow.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache incluye los ads del feed
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_invalidates_feed_ads_keys(mock_run, uc, mock_cache):
    """Sacar de `active` una property promocionada la dejaba sirviéndose como
    aviso pago hasta que expirara el TTL de esa entrada."""
    mock_run.return_value = _make_mock_prop(ListingStatus.active)

    await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.inactive)

    deleted_keys = mock_cache.delete.call_args.kwargs["key"]
    assert feed_ads_global() in deleted_keys
    assert feed_ads_by_city(CITY_ID) in deleted_keys


@patch("app.services.admin.use_cases.moderation.set_status.run_in_threadpool")
async def test_invalidates_ads_without_asking_if_promoted(mock_run, uc, mock_cache, mock_uow):
    """Averiguarlo costaría una query por cada cambio de status; borrar una key
    que se repuebla sola en el primer feed sale más barato."""
    mock_run.return_value = _make_mock_prop(ListingStatus.draft)

    await uc.execute(principal=ADMIN, property_id=PROP_ID, target_status=ListingStatus.active)

    assert mock_run.await_count == 1  # solo el get_by_id, ninguna consulta de promociones
    assert feed_ads_global() in mock_cache.delete.call_args.kwargs["key"]
