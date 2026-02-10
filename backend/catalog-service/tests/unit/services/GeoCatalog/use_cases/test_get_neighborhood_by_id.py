import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.geo_catalog.use_cases.get_neighborhood_by_id import GetNeighborhoodByIdUseCase
from app.core.exceptions.geo_catalog import NeighborhoodNotFoundError

NEIGHBORHOOD_ID = uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890')

NEIGHBORHOOD = MagicMock()
NEIGHBORHOOD.model_dump.return_value = {"id": str(NEIGHBORHOOD_ID), "name": "Chapinero"}


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.neighborhoods.get_active_by_id.return_value = NEIGHBORHOOD
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return GetNeighborhoodByIdUseCase(uow=mock_uow, cache_client=mock_cache)


@pytest.mark.asyncio
async def test_returns_from_db_on_cache_miss(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None

    result = await uc.execute(neighborhood_id=NEIGHBORHOOD_ID)

    assert result == NEIGHBORHOOD
    mock_cache.get_json.assert_awaited_once()
    mock_uow.neighborhoods.get_active_by_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.geo_catalog.use_cases.get_neighborhood_by_id.Neighborhood")
async def test_returns_from_cache_when_available(mock_neighborhood_cls, uc, mock_uow, mock_cache):
    cached_data = {"id": str(NEIGHBORHOOD_ID), "name": "Chapinero"}
    mock_cache.get_json.return_value = cached_data
    mock_neighborhood_cls.model_validate.return_value = NEIGHBORHOOD

    result = await uc.execute(neighborhood_id=NEIGHBORHOOD_ID)

    assert result == NEIGHBORHOOD
    mock_cache.get_json.assert_awaited_once()
    mock_neighborhood_cls.model_validate.assert_called_once_with(cached_data)
    mock_uow.neighborhoods.get_active_by_id.assert_not_called()
    mock_cache.set_json.assert_not_called()


@pytest.mark.asyncio
async def test_survives_cache_get_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.side_effect = Exception("Redis connection refused")

    result = await uc.execute(neighborhood_id=NEIGHBORHOOD_ID)

    assert result == NEIGHBORHOOD
    mock_cache.get_json.assert_awaited_once()
    mock_uow.neighborhoods.get_active_by_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_survives_cache_set_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None
    mock_cache.set_json.side_effect = Exception("Redis connection refused")

    result = await uc.execute(neighborhood_id=NEIGHBORHOOD_ID)

    assert result == NEIGHBORHOOD
    mock_cache.get_json.assert_awaited_once()
    mock_uow.neighborhoods.get_active_by_id.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_raises_not_found_when_neighborhood_missing(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None
    mock_uow.neighborhoods.get_active_by_id.return_value = None

    with pytest.raises(NeighborhoodNotFoundError):
        await uc.execute(neighborhood_id=NEIGHBORHOOD_ID)

    mock_cache.set_json.assert_not_called()
