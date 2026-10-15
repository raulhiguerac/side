import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions.catalog_admin import CatalogAdminDbUnavailableError
from app.services.catalog_admin.schemas.admin_division import (
    AdminDivisionResponse,
    GetAllAdminDivisionsRequest,
)
from app.services.catalog_admin.use_cases.admin_division.list_all import (
    ListAdminDivisionsUseCase,
)

COUNTRY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_DIVISION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def _make_db_admin_division():
    m = MagicMock()
    m.id = ADMIN_DIVISION_ID
    m.country_id = COUNTRY_ID
    m.code = "11"
    m.iso_code = "CO-DC"
    m.name = "Bogotá D.C."
    m.type_name = "Distrito Capital"
    m.is_active = False
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.admin_divisions.get_all.return_value = [_make_db_admin_division()]
    uow.admin_divisions.count_all.return_value = 33
    return uow


@pytest.fixture
def uc(mock_uow):
    return ListAdminDivisionsUseCase(uow=mock_uow)


@pytest.mark.asyncio
async def test_builds_page_from_repository(uc, mock_uow):
    req = GetAllAdminDivisionsRequest(page=2, page_size=20, country_id=COUNTRY_ID, is_active=False)

    page = await uc.execute(req=req)

    assert page.items == [
        AdminDivisionResponse(
            id=ADMIN_DIVISION_ID,
            country_id=COUNTRY_ID,
            code="11",
            iso_code="CO-DC",
            name="Bogotá D.C.",
            type_name="Distrito Capital",
            is_active=False,
        )
    ]
    assert page.total_items == 33
    assert page.total_pages == 2
    assert page.current_page == 2
    assert page.items_per_page == 20
    mock_uow.admin_divisions.get_all.assert_called_once_with(filters=req)
    mock_uow.admin_divisions.count_all.assert_called_once_with(filters=req)


@pytest.mark.asyncio
async def test_empty_result_has_zero_pages(uc, mock_uow):
    mock_uow.admin_divisions.get_all.return_value = []
    mock_uow.admin_divisions.count_all.return_value = 0

    page = await uc.execute(req=GetAllAdminDivisionsRequest())

    assert page.items == []
    assert page.total_items == 0
    assert page.total_pages == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("failing", ["get_all", "count_all"])
async def test_db_unavailable_in_any_query_is_translated(uc, mock_uow, failing):
    getattr(mock_uow.admin_divisions, failing).side_effect = OperationalError("SELECT", {}, Exception("down"))

    with pytest.raises(CatalogAdminDbUnavailableError):
        await uc.execute(req=GetAllAdminDivisionsRequest())


@pytest.mark.asyncio
async def test_non_db_errors_are_not_masked(uc, mock_uow):
    mock_uow.admin_divisions.get_all.side_effect = ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await uc.execute(req=GetAllAdminDivisionsRequest())
