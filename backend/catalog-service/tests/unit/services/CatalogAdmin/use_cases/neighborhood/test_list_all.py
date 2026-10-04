import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions.catalog_admin import CatalogAdminDbUnavailableError
from app.services.catalog_admin.schemas.neighborhood import (
    ListNeighborhoodsAdminRequest,
    NeighborhoodAdminListItem,
    NeighborhoodCoverage,
)
from app.services.catalog_admin.use_cases.neighborhood.list_all import (
    ListNeighborhoodsUseCase,
)

LOCALITY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

ITEM = NeighborhoodAdminListItem(
    id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    locality_id=LOCALITY_ID,
    code="0231",
    name="Chico Norte",
    is_active=True,
    has_geometry=True,
    svg_path="M -74.04 -4.67 l 0.001 0.001 z",
    bbox=(-74.05, 4.66, -74.03, 4.68),
)
COVERAGE = NeighborhoodCoverage(with_geometry=38, total=42)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.neighborhoods.get_all.return_value = [ITEM]
    uow.neighborhoods.count_all.return_value = 41
    uow.neighborhoods.get_coverage.return_value = COVERAGE
    return uow


@pytest.fixture
def uc(mock_uow):
    return ListNeighborhoodsUseCase(uow=mock_uow)


@pytest.mark.asyncio
async def test_builds_page_from_repository(uc, mock_uow):
    req = ListNeighborhoodsAdminRequest(page=2, page_size=20, locality_id=LOCALITY_ID)

    page = await uc.execute(req=req)

    assert page.items == [ITEM]
    assert page.total_items == 41
    assert page.total_pages == 3
    assert page.current_page == 2
    assert page.items_per_page == 20
    assert page.coverage == COVERAGE
    mock_uow.neighborhoods.get_all.assert_called_once_with(req=req)
    mock_uow.neighborhoods.count_all.assert_called_once_with(req=req)
    mock_uow.neighborhoods.get_coverage.assert_called_once_with(req=req)


@pytest.mark.asyncio
async def test_empty_result_has_zero_pages(uc, mock_uow):
    mock_uow.neighborhoods.get_all.return_value = []
    mock_uow.neighborhoods.count_all.return_value = 0

    page = await uc.execute(req=ListNeighborhoodsAdminRequest(has_geometry=False))

    assert page.items == []
    assert page.total_items == 0
    assert page.total_pages == 0


@pytest.mark.asyncio
async def test_db_unavailable_is_translated(uc, mock_uow):
    mock_uow.neighborhoods.get_all.side_effect = OperationalError("SELECT", {}, Exception("down"))

    with pytest.raises(CatalogAdminDbUnavailableError):
        await uc.execute(req=ListNeighborhoodsAdminRequest())


@pytest.mark.asyncio
async def test_exact_division_does_not_add_a_page(uc, mock_uow):
    mock_uow.neighborhoods.count_all.return_value = 40

    page = await uc.execute(req=ListNeighborhoodsAdminRequest(page_size=20))

    assert page.total_pages == 2


@pytest.mark.asyncio
async def test_page_out_of_range_keeps_real_totals(uc, mock_uow):
    mock_uow.neighborhoods.get_all.return_value = []

    page = await uc.execute(req=ListNeighborhoodsAdminRequest(page=5, page_size=20))

    assert page.items == []
    assert page.total_items == 41
    assert page.total_pages == 3
    assert page.current_page == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("failing", ["count_all", "get_coverage"])
async def test_db_unavailable_in_any_query_is_translated(uc, mock_uow, failing):
    getattr(mock_uow.neighborhoods, failing).side_effect = OperationalError("SELECT", {}, Exception("down"))

    with pytest.raises(CatalogAdminDbUnavailableError):
        await uc.execute(req=ListNeighborhoodsAdminRequest())


@pytest.mark.asyncio
async def test_non_db_errors_are_not_masked(uc, mock_uow):
    mock_uow.neighborhoods.get_all.side_effect = ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await uc.execute(req=ListNeighborhoodsAdminRequest())
