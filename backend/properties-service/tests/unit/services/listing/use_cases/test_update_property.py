import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import CreatePropertyError, PropertyForbiddenError, PropertyNotFoundError
from app.models.listing import Currency, ListingStatus, ListingType, PropertyCondition, PropertyType, VerificationStatus
from app.schemas.principal import Principal
from app.services.listing.schemas.listing_schemas import UpdatePropertyRequest
from app.services.listing.use_cases.property_core.update_property import UpdatePropertyUseCase

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

PRINCIPAL = Principal(sub=OWNER_ID)


def _make_mock_prop():
    m = MagicMock()
    m.id = PROP_ID
    m.owner_id = OWNER_ID
    m.status = ListingStatus.draft
    m.location = None
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.refresh = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return UpdatePropertyUseCase(
        uow = mock_uow,
        cache_client = mock_cache,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.update_property.get_owned_property", new_callable=AsyncMock)
async def test_updates_fields_and_commits(mock_get_prop, uc, mock_uow, mock_cache):
    prop = _make_mock_prop()
    mock_get_prop.return_value = prop
    request = UpdatePropertyRequest(price=Decimal("200000.00"))

    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, request=request)

    assert prop.price == Decimal("200000.00")
    assert prop.updated_by == OWNER_ID
    mock_uow.commit.assert_awaited_once()
    mock_uow.refresh.assert_awaited_once_with(prop)
    mock_cache.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# Property not found / forbidden
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.update_property.get_owned_property", new_callable=AsyncMock)
async def test_raises_not_found(mock_get_prop, uc, mock_uow):
    mock_get_prop.side_effect = PropertyNotFoundError(property_id=PROP_ID)

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, request=UpdatePropertyRequest())

    mock_uow.commit.assert_not_awaited()


@patch("app.services.listing.use_cases.property_core.update_property.get_owned_property", new_callable=AsyncMock)
async def test_raises_forbidden(mock_get_prop, uc, mock_uow):
    mock_get_prop.side_effect = PropertyForbiddenError(property_id=PROP_ID)

    with pytest.raises(PropertyForbiddenError):
        await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, request=UpdatePropertyRequest())

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.update_property.translate_db_error")
@patch("app.services.listing.use_cases.property_core.update_property.get_owned_property", new_callable=AsyncMock)
async def test_rolls_back_and_raises_on_commit_error(mock_get_prop, mock_translate, uc, mock_uow, mock_cache):
    mock_get_prop.return_value = _make_mock_prop()
    mock_uow.commit.side_effect = Exception("db error")
    mock_translate.return_value = CreatePropertyError(cause=Exception("db error"))

    with pytest.raises(CreatePropertyError):
        await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, request=UpdatePropertyRequest())

    mock_uow.rollback.assert_awaited_once()
    mock_cache.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.update_property.get_owned_property", new_callable=AsyncMock)
async def test_survives_cache_delete_failure(mock_get_prop, uc, mock_uow, mock_cache):
    mock_get_prop.return_value = _make_mock_prop()
    mock_cache.delete.side_effect = Exception("Redis down")

    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, request=UpdatePropertyRequest())

    mock_uow.commit.assert_awaited_once()
