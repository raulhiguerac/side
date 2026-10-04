import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions.catalog_admin import (
    CatalogAdminDbUnavailableError,
    NeighborhoodAdminNotFoundError,
)
from app.services.catalog_admin.schemas.neighborhood import NeighborhoodAdminDetail
from app.services.catalog_admin.use_cases.neighborhood.get_detail import (
    GetNeighborhoodDetailUseCase,
)

NEIGHBORHOOD_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

DETAIL = NeighborhoodAdminDetail(
    id=NEIGHBORHOOD_ID,
    locality_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    code="0231",
    name="Chico Norte",
    postal_code=None,
    latitude=4.6789,
    longitude=-74.0467,
    is_active=True,
    geometry={"type": "Polygon", "coordinates": []},
    area_m2=971046.0,
)


@pytest.fixture
def mock_uow():
    return MagicMock()


@pytest.fixture
def uc(mock_uow):
    return GetNeighborhoodDetailUseCase(uow=mock_uow)


@pytest.mark.asyncio
async def test_returns_detail(uc, mock_uow):
    mock_uow.neighborhoods.get_detail.return_value = DETAIL

    result = await uc.execute(neighborhood_id=NEIGHBORHOOD_ID)

    assert result == DETAIL
    mock_uow.neighborhoods.get_detail.assert_called_once_with(neighborhood_id=NEIGHBORHOOD_ID)


@pytest.mark.asyncio
async def test_raises_not_found_when_missing(uc, mock_uow):
    mock_uow.neighborhoods.get_detail.return_value = None

    with pytest.raises(NeighborhoodAdminNotFoundError):
        await uc.execute(neighborhood_id=NEIGHBORHOOD_ID)


@pytest.mark.asyncio
async def test_db_unavailable_is_translated(uc, mock_uow):
    mock_uow.neighborhoods.get_detail.side_effect = OperationalError("SELECT", {}, Exception("down"))

    with pytest.raises(CatalogAdminDbUnavailableError):
        await uc.execute(neighborhood_id=NEIGHBORHOOD_ID)
