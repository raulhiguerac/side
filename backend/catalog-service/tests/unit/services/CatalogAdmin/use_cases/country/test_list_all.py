import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from app.core.exceptions.catalog_admin import CatalogAdminDbUnavailableError
from app.services.catalog_admin.schemas.country import (
    GetAllCountriesRequest,
    GetAllCountriesResponse,
)
from app.services.catalog_admin.use_cases.country.list_all import ListCountriesUseCase

COUNTRY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _make_db_country():
    m = MagicMock()
    m.id = COUNTRY_ID
    m.iso_alpha2 = "CO"
    m.iso_alpha3 = "COL"
    m.iso_numeric = "170"
    m.name = "Colombia"
    m.official_name = "República de Colombia"
    m.native_name = None
    m.phone_code = "+57"
    m.currency_code = "COP"
    m.default_locale = "es"
    m.default_timezone = "America/Bogota"
    m.is_active = False
    m.is_supported = True
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.countries.get_all.return_value = [_make_db_country()]
    uow.countries.count_all.return_value = 21
    return uow


@pytest.fixture
def uc(mock_uow):
    return ListCountriesUseCase(uow=mock_uow)


@pytest.mark.asyncio
async def test_builds_page_from_repository(uc, mock_uow):
    req = GetAllCountriesRequest(page=1, page_size=20, is_active=False, is_supported=True)

    page = await uc.execute(req=req)

    assert page.items == [
        GetAllCountriesResponse(
            id=COUNTRY_ID,
            iso_alpha2="CO",
            iso_alpha3="COL",
            iso_numeric="170",
            name="Colombia",
            official_name="República de Colombia",
            native_name=None,
            phone_code="+57",
            currency_code="COP",
            default_locale="es",
            default_timezone="America/Bogota",
            is_active=False,
            is_supported=True,
        )
    ]
    assert page.total_items == 21
    assert page.total_pages == 2
    assert page.current_page == 1
    assert page.items_per_page == 20
    mock_uow.countries.get_all.assert_called_once_with(filters=req)
    mock_uow.countries.count_all.assert_called_once_with(filters=req)


@pytest.mark.asyncio
async def test_empty_result_has_zero_pages(uc, mock_uow):
    mock_uow.countries.get_all.return_value = []
    mock_uow.countries.count_all.return_value = 0

    page = await uc.execute(req=GetAllCountriesRequest())

    assert page.items == []
    assert page.total_items == 0
    assert page.total_pages == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("failing", ["get_all", "count_all"])
async def test_db_unavailable_in_any_query_is_translated(uc, mock_uow, failing):
    getattr(mock_uow.countries, failing).side_effect = OperationalError("SELECT", {}, Exception("down"))

    with pytest.raises(CatalogAdminDbUnavailableError):
        await uc.execute(req=GetAllCountriesRequest())


@pytest.mark.asyncio
async def test_non_db_errors_are_not_masked(uc, mock_uow):
    mock_uow.countries.get_all.side_effect = ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await uc.execute(req=GetAllCountriesRequest())
