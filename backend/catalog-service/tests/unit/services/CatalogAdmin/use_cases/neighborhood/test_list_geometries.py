import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions.catalog_admin import CatalogAdminDbUnavailableError
from app.services.catalog_admin.schemas.neighborhood import (
    ListNeighborhoodGeometriesRequest,
    NeighborhoodGeometryItem,
)
from app.services.catalog_admin.use_cases.neighborhood.list_geometries import (
    ListNeighborhoodGeometriesUseCase,
)

REQUEST = ListNeighborhoodGeometriesRequest(
    neighborhood_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    bbox=(-74.06, 4.67, -74.03, 4.69),
)

NEIGHBOR = NeighborhoodGeometryItem(
    id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    name="El Chico",
    geometry={"type": "Polygon", "coordinates": []},
)


@pytest.fixture
def mock_uow():
    return MagicMock()


@pytest.fixture
def uc(mock_uow):
    return ListNeighborhoodGeometriesUseCase(uow=mock_uow)


@pytest.mark.asyncio
async def test_returns_neighbors_from_repository(uc, mock_uow):
    mock_uow.neighborhoods.get_geometries.return_value = [NEIGHBOR]

    result = await uc.execute(req=REQUEST)

    assert result == [NEIGHBOR]
    mock_uow.neighborhoods.get_geometries.assert_called_once_with(req=REQUEST)


@pytest.mark.asyncio
async def test_empty_area_returns_empty_list(uc, mock_uow):
    mock_uow.neighborhoods.get_geometries.return_value = []

    assert await uc.execute(req=REQUEST) == []


@pytest.mark.asyncio
async def test_db_unavailable_is_translated(uc, mock_uow):
    mock_uow.neighborhoods.get_geometries.side_effect = OperationalError("SELECT", {}, Exception("down"))

    with pytest.raises(CatalogAdminDbUnavailableError):
        await uc.execute(req=REQUEST)
