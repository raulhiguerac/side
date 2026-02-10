import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.geo_catalog.schemas.neighborhood import NeighborhoodListItem
from app.services.geo_catalog.use_cases.get_neighborhoods_by_locality import GetNeighborhoodsByLocalityUseCase

LOCALITY_ID = uuid.UUID('86f1f356-e83a-47f4-b50b-0cf7bb5d9ac5')

NEIGHBORHOOD_LIST = [
    NeighborhoodListItem(
        id=uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890'),
        locality_id=LOCALITY_ID,
        name='Chapinero',
        search_name='chapinero',
        latitude=4.6486,
        longitude=-74.0628,
    ),
    NeighborhoodListItem(
        id=uuid.UUID('b2c3d4e5-f6a7-8901-bcde-f12345678901'),
        locality_id=LOCALITY_ID,
        name='Usaquén',
        search_name='usaquen',
        latitude=4.6966,
        longitude=-74.0324,
    ),
]


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.neighborhoods.get_active_by_locality_id.return_value = NEIGHBORHOOD_LIST
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return GetNeighborhoodsByLocalityUseCase(uow=mock_uow, cache_client=mock_cache)


@pytest.mark.asyncio
async def test_returns_from_db_on_cache_miss(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None

    result = await uc.execute(locality_id=LOCALITY_ID)

    assert result == NEIGHBORHOOD_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.neighborhoods.get_active_by_locality_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_from_cache_when_available(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = [item.model_dump() for item in NEIGHBORHOOD_LIST]

    result = await uc.execute(locality_id=LOCALITY_ID)

    assert result == NEIGHBORHOOD_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.neighborhoods.get_active_by_locality_id.assert_not_called()
    mock_cache.set_json.assert_not_called()


@pytest.mark.asyncio
async def test_survives_cache_get_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.side_effect = Exception("Redis connection refused")

    result = await uc.execute(locality_id=LOCALITY_ID)

    assert result == NEIGHBORHOOD_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.neighborhoods.get_active_by_locality_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_survives_cache_set_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None
    mock_cache.set_json.side_effect = Exception("Redis connection refused")

    result = await uc.execute(locality_id=LOCALITY_ID)

    assert result == NEIGHBORHOOD_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.neighborhoods.get_active_by_locality_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_empty_list_when_no_neighborhoods(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None
    mock_uow.neighborhoods.get_active_by_locality_id.return_value = []

    result = await uc.execute(locality_id=LOCALITY_ID)

    assert result == []
    mock_cache.set_json.assert_awaited_once()
