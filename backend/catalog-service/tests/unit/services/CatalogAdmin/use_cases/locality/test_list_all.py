import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app.core.exceptions.catalog_admin import CatalogAdminDbUnavailableError
from app.models.location import LocalityType
from app.services.catalog_admin.schemas.locality import (
    GetAllLocalitiesRequest,
    GetAllLocalitiesResponse,
    LocalityPoint,
)
from app.services.catalog_admin.use_cases.locality.list_all import ListLocalitiesUseCase

COUNTRY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_DIVISION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
LOCALITY_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


def _make_db_locality():
    m = MagicMock()
    m.id = LOCALITY_ID
    m.country_id = COUNTRY_ID
    m.admin_division_id = ADMIN_DIVISION_ID
    m.code = "BOG"
    m.name = "Bogotá"
    m.local_name = "Bogotá D.C."
    m.locality_type = LocalityType.city
    m.latitude = 4.7110
    m.longitude = -74.0721
    m.timezone = "America/Bogota"
    m.is_active = False
    m.is_capital = True
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.localities.get_all.return_value = [_make_db_locality()]
    uow.localities.count_all.return_value = 41
    return uow


@pytest.fixture
def uc(mock_uow):
    return ListLocalitiesUseCase(uow=mock_uow)


@pytest.mark.asyncio
async def test_builds_page_from_repository(uc, mock_uow):
    req = GetAllLocalitiesRequest(page=2, page_size=20, country_id=COUNTRY_ID, admin_division_id=ADMIN_DIVISION_ID)

    page = await uc.execute(req=req)

    assert page.items == [
        GetAllLocalitiesResponse(
            id=LOCALITY_ID,
            country_id=COUNTRY_ID,
            admin_division_id=ADMIN_DIVISION_ID,
            code="BOG",
            name="Bogotá",
            local_name="Bogotá D.C.",
            locality_type=LocalityType.city,
            point=LocalityPoint(latitude=4.7110, longitude=-74.0721),
            timezone="America/Bogota",
            is_active=False,
            is_capital=True,
        )
    ]
    assert page.total_items == 41
    assert page.total_pages == 3
    assert page.current_page == 2
    assert page.items_per_page == 20
    mock_uow.localities.get_all.assert_called_once_with(filters=req)
    mock_uow.localities.count_all.assert_called_once_with(filters=req)


@pytest.mark.asyncio
async def test_empty_result_has_zero_pages(uc, mock_uow):
    mock_uow.localities.get_all.return_value = []
    mock_uow.localities.count_all.return_value = 0

    page = await uc.execute(req=GetAllLocalitiesRequest(is_active=True))

    assert page.items == []
    assert page.total_items == 0
    assert page.total_pages == 0


@pytest.mark.asyncio
async def test_exact_division_does_not_add_a_page(uc, mock_uow):
    mock_uow.localities.count_all.return_value = 40

    page = await uc.execute(req=GetAllLocalitiesRequest(page_size=20))

    assert page.total_pages == 2


@pytest.mark.asyncio
async def test_page_out_of_range_keeps_real_totals(uc, mock_uow):
    mock_uow.localities.get_all.return_value = []

    page = await uc.execute(req=GetAllLocalitiesRequest(page=5, page_size=20))

    assert page.items == []
    assert page.total_items == 41
    assert page.total_pages == 3
    assert page.current_page == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("failing", ["get_all", "count_all"])
async def test_db_unavailable_in_any_query_is_translated(uc, mock_uow, failing):
    getattr(mock_uow.localities, failing).side_effect = OperationalError("SELECT", {}, Exception("down"))

    with pytest.raises(CatalogAdminDbUnavailableError):
        await uc.execute(req=GetAllLocalitiesRequest())


@pytest.mark.asyncio
async def test_non_db_errors_are_not_masked(uc, mock_uow):
    mock_uow.localities.get_all.side_effect = ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await uc.execute(req=GetAllLocalitiesRequest())


@pytest.mark.parametrize(("page", "page_size", "offset"), [(1, 20, 0), (3, 20, 40), (2, 50, 50)])
def test_offset_is_derived_from_page(page, page_size, offset):
    assert GetAllLocalitiesRequest(page=page, page_size=page_size).offset == offset


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}, {"offset": 40}])
def test_rejects_invalid_pagination(params):
    with pytest.raises(ValidationError):
        GetAllLocalitiesRequest(**params)
