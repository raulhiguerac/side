import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions.catalog_admin import CountryNotFoundError, CountryConflictError
from app.services.catalog_admin.schemas.country import UpdateCountryRequest, CountryResponse
from app.services.catalog_admin.use_cases.update_country import UpdateCountryUseCase

COUNTRY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

REQUEST = UpdateCountryRequest(name="República de Colombia", is_active=True)


def _make_db_country():
    m = MagicMock()
    m.id = COUNTRY_ID
    m.iso_alpha2 = "CO"
    m.iso_alpha3 = "COL"
    m.name = "República de Colombia"
    m.phone_code = "+57"
    m.currency_code = "COP"
    m.default_timezone = "America/Bogota"
    m.is_active = True
    m.is_supported = False
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.refresh = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return UpdateCountryUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_country.run_in_threadpool")
async def test_updates_country_caches_fresh_data(mock_run, uc, mock_uow, mock_cache):
    country = _make_db_country()
    mock_run.return_value = country

    result = await uc.execute(country_id=COUNTRY_ID, request=REQUEST)

    assert isinstance(result, CountryResponse)
    mock_uow.commit.assert_awaited_once()
    mock_uow.refresh.assert_awaited_once_with(country)
    mock_cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_country.run_in_threadpool")
async def test_raises_not_found_when_country_missing(mock_run, uc, mock_uow):
    mock_run.return_value = None

    with pytest.raises(CountryNotFoundError):
        await uc.execute(country_id=COUNTRY_ID, request=REQUEST)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_country.translate_db_error")
@patch("app.services.catalog_admin.use_cases.update_country.run_in_threadpool")
async def test_rolls_back_and_raises_on_db_error(mock_run, mock_translate, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_country()
    mock_uow.commit.side_effect = Exception("unique constraint")
    mock_translate.return_value = CountryConflictError(field="name", value="República de Colombia")

    with pytest.raises(CountryConflictError):
        await uc.execute(country_id=COUNTRY_ID, request=REQUEST)

    mock_uow.rollback.assert_awaited_once()
    mock_cache.set_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_country.run_in_threadpool")
async def test_survives_cache_failure(mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_country()
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute(country_id=COUNTRY_ID, request=REQUEST)

    assert isinstance(result, CountryResponse)
    mock_uow.commit.assert_awaited_once()
