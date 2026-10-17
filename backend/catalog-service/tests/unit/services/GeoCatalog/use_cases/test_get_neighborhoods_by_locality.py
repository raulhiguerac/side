import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.geo_catalog.schemas.neighborhood import NeighborhoodListItem
from app.services.geo_catalog.use_cases.get_neighborhoods_by_locality import (
    GetNeighborhoodsByLocalityUseCase,
)
from app.services.shared.helpers.cache_keys import cache_key_neighborhoods

LOCALITY_ID = uuid.UUID('86f1f356-e83a-47f4-b50b-0cf7bb5d9ac5')
OTHER_LOCALITY_ID = uuid.UUID('cbb6be87-f505-4559-8d52-2c4f23bb7cb1')

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

OTHER_NEIGHBORHOOD = NeighborhoodListItem(
    id=uuid.UUID('c3d4e5f6-a7b8-9012-cdef-123456789012'),
    locality_id=OTHER_LOCALITY_ID,
    name='El Poblado',
    search_name='el poblado',
    latitude=6.2088,
    longitude=-75.5674,
)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.neighborhoods.get_active_by_locality_ids.return_value = NEIGHBORHOOD_LIST
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

    result = await uc.execute(locality_ids=[LOCALITY_ID])

    assert result.neighborhoods == {str(LOCALITY_ID): NEIGHBORHOOD_LIST}
    mock_cache.get_json.assert_awaited_once_with(key=cache_key_neighborhoods(locality_id=LOCALITY_ID))
    mock_uow.neighborhoods.get_active_by_locality_ids.assert_called_once_with(locality_ids=[LOCALITY_ID])
    mock_cache.set_json.assert_awaited_once()
    assert mock_cache.set_json.await_args.kwargs['key'] == cache_key_neighborhoods(locality_id=LOCALITY_ID)


@pytest.mark.asyncio
async def test_returns_from_cache_when_available(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = [item.model_dump(mode='json') for item in NEIGHBORHOOD_LIST]

    result = await uc.execute(locality_ids=[LOCALITY_ID])

    assert result.neighborhoods == {str(LOCALITY_ID): NEIGHBORHOOD_LIST}
    mock_uow.neighborhoods.get_active_by_locality_ids.assert_not_called()
    mock_cache.set_json.assert_not_called()


@pytest.mark.asyncio
async def test_queries_db_only_for_cache_misses(uc, mock_uow, mock_cache):
    cached = [item.model_dump(mode='json') for item in NEIGHBORHOOD_LIST]
    mock_cache.get_json.side_effect = [cached, None]
    mock_uow.neighborhoods.get_active_by_locality_ids.return_value = [OTHER_NEIGHBORHOOD]

    result = await uc.execute(locality_ids=[LOCALITY_ID, OTHER_LOCALITY_ID])

    assert result.neighborhoods == {
        str(LOCALITY_ID): NEIGHBORHOOD_LIST,
        str(OTHER_LOCALITY_ID): [OTHER_NEIGHBORHOOD],
    }
    mock_uow.neighborhoods.get_active_by_locality_ids.assert_called_once_with(locality_ids=[OTHER_LOCALITY_ID])
    mock_cache.set_json.assert_awaited_once()
    assert mock_cache.set_json.await_args.kwargs['key'] == cache_key_neighborhoods(locality_id=OTHER_LOCALITY_ID)


@pytest.mark.asyncio
async def test_caches_empty_list_when_no_neighborhoods(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None
    mock_uow.neighborhoods.get_active_by_locality_ids.return_value = []

    result = await uc.execute(locality_ids=[LOCALITY_ID])

    assert result.neighborhoods == {}
    mock_cache.set_json.assert_awaited_once()
    assert mock_cache.set_json.await_args.kwargs['value'] == []


@pytest.mark.asyncio
async def test_survives_cache_get_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.side_effect = Exception("Redis connection refused")

    result = await uc.execute(locality_ids=[LOCALITY_ID])

    assert result.neighborhoods == {str(LOCALITY_ID): NEIGHBORHOOD_LIST}
    mock_uow.neighborhoods.get_active_by_locality_ids.assert_called_once_with(locality_ids=[LOCALITY_ID])


@pytest.mark.asyncio
async def test_survives_cache_set_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None
    mock_cache.set_json.side_effect = Exception("Redis connection refused")

    result = await uc.execute(locality_ids=[LOCALITY_ID])

    assert result.neighborhoods == {str(LOCALITY_ID): NEIGHBORHOOD_LIST}
    mock_cache.set_json.assert_awaited_once()
