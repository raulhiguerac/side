import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import DeletePropertyError, PropertyForbiddenError, PropertyNotFoundError
from app.models.listing import ListingStatus
from app.schemas.principal import Principal
from app.services.listing.use_cases.property_core.delete_property import DeletePropertyUseCase

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
PRINCIPAL = Principal(sub=OWNER_ID)


def _make_mock_prop():
    m = MagicMock()
    m.id = PROP_ID
    m.owner_id = OWNER_ID
    m.status = ListingStatus.active
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
    return DeletePropertyUseCase(cache=mock_cache, uow=mock_uow)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.delete_property.get_owned_property", new_callable=AsyncMock)
async def test_marks_property_inactive_and_soft_deletes(mock_get_prop, uc, mock_uow, mock_cache):
    prop = _make_mock_prop()
    mock_get_prop.return_value = prop

    await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    assert prop.status == ListingStatus.inactive
    assert prop.deleted_by == OWNER_ID
    assert prop.deleted_at is not None
    mock_uow.commit.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# Not found / forbidden
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.delete_property.get_owned_property", new_callable=AsyncMock)
async def test_raises_not_found(mock_get_prop, uc, mock_uow):
    mock_get_prop.side_effect = PropertyNotFoundError(property_id=PROP_ID)

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    mock_uow.commit.assert_not_awaited()


@patch("app.services.listing.use_cases.property_core.delete_property.get_owned_property", new_callable=AsyncMock)
async def test_raises_forbidden(mock_get_prop, uc, mock_uow):
    mock_get_prop.side_effect = PropertyForbiddenError(property_id=PROP_ID)

    with pytest.raises(PropertyForbiddenError):
        await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.delete_property.get_owned_property", new_callable=AsyncMock)
async def test_rolls_back_and_raises_delete_error_on_commit_failure(mock_get_prop, uc, mock_uow):
    mock_get_prop.return_value = _make_mock_prop()
    mock_uow.commit.side_effect = Exception("db error")

    with pytest.raises(DeletePropertyError):
        await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    mock_uow.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.delete_property.get_owned_property", new_callable=AsyncMock)
async def test_survives_cache_delete_failure(mock_get_prop, uc, mock_uow, mock_cache):
    mock_get_prop.return_value = _make_mock_prop()
    mock_cache.delete.side_effect = Exception("Redis down")

    await uc.execute(property_id=PROP_ID, principal=PRINCIPAL)

    mock_uow.commit.assert_awaited_once()
