import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.geo_catalog.schemas.locality import LocalityListItem, AdminDivisionRef
from app.services.geo_catalog.use_cases.get_locality import GetLocalitiesUseCase

COUNTRY_ID = uuid.UUID('8b37f57c-ed32-434b-98fd-2afa4caed634')
ADMIN_DIVISION_ID = uuid.UUID('d4f1a2b3-c5e6-7890-abcd-ef1234567890')

LOCALITY_LIST = [
    LocalityListItem(
        id=uuid.UUID('86f1f356-e83a-47f4-b50b-0cf7bb5d9ac5'),
        name='Bogota',
        admin_division=AdminDivisionRef(id=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), name='Cundinamarca'),
    ),
    LocalityListItem(
        id=uuid.UUID('cbb6be87-f505-4559-8d52-2c4f23bb7cb1'),
        name='Medellin',
        admin_division=AdminDivisionRef(id=uuid.UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'), name='Antioquia'),
    ),
]


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.localities.get_active_by_country_id.return_value = LOCALITY_LIST
    uow.localities.get_active_by_admin_division_id.return_value = LOCALITY_LIST
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return GetLocalitiesUseCase(uow=mock_uow, cache_client=mock_cache)


@pytest.mark.asyncio
async def test_returns_from_db_on_cache_miss(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None

    result = await uc.execute(country_id=COUNTRY_ID)

    assert result == LOCALITY_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.localities.get_active_by_country_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_from_cache_when_available(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = [item.model_dump() for item in LOCALITY_LIST]

    result = await uc.execute(country_id=COUNTRY_ID)

    assert result == LOCALITY_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.localities.get_active_by_country_id.assert_not_called()
    mock_cache.set_json.assert_not_called()


@pytest.mark.asyncio
async def test_survives_cache_get_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.side_effect = Exception("Redis connection refused")

    result = await uc.execute(country_id=COUNTRY_ID)

    assert result == LOCALITY_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.localities.get_active_by_country_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_survives_cache_set_failure(uc, mock_uow, mock_cache):
    """Si Redis falla en SET, debe retornar data igual."""
    mock_cache.get_json.return_value = None
    mock_cache.set_json.side_effect = Exception("Redis connection refused")

    result = await uc.execute(country_id=COUNTRY_ID)

    assert result == LOCALITY_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.localities.get_active_by_country_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_empty_list_when_no_localities(uc, mock_uow, mock_cache):
    """País sin localidades devuelve lista vacía."""
    mock_cache.get_json.return_value = None
    mock_uow.localities.get_active_by_country_id.return_value = []

    result = await uc.execute(country_id=COUNTRY_ID)

    assert result == []
    mock_cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# admin_division_id path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_returns_from_db_by_admin_division_on_cache_miss(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None

    result = await uc.execute(admin_division_id=ADMIN_DIVISION_ID)

    assert result == LOCALITY_LIST
    mock_uow.localities.get_active_by_admin_division_id.assert_called_once()
    mock_uow.localities.get_active_by_country_id.assert_not_called()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_from_cache_by_admin_division(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = [item.model_dump() for item in LOCALITY_LIST]

    result = await uc.execute(admin_division_id=ADMIN_DIVISION_ID)

    assert result == LOCALITY_LIST
    mock_uow.localities.get_active_by_admin_division_id.assert_not_called()
    mock_cache.set_json.assert_not_called()
