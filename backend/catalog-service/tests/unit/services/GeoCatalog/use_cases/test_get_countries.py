import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.geo_catalog.schemas.country import CountryListItem
from app.services.geo_catalog.use_cases.get_countries import GetCountriesUseCase

COUNTRY_LIST = [
    CountryListItem(
        id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        name="Colombia",
        iso_alpha2="CO",
        phone_code="+57",
        is_supported=True,
    ),
    CountryListItem(
        id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        name="México",
        iso_alpha2="MX",
        phone_code="+52",
        is_supported=False,
    ),
]


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.countries.get_active_countries.return_value = COUNTRY_LIST
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return GetCountriesUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Cache miss → DB
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_returns_from_db_on_cache_miss(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None

    result = await uc.execute()

    assert result == COUNTRY_LIST
    mock_cache.get_json.assert_awaited_once()
    mock_uow.countries.get_active_countries.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache hit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_returns_from_cache_when_available(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = [item.model_dump() for item in COUNTRY_LIST]

    result = await uc.execute()

    assert result == COUNTRY_LIST
    mock_uow.countries.get_active_countries.assert_not_called()
    mock_cache.set_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache get failure → fallback DB
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_survives_cache_get_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.side_effect = Exception("Redis down")

    result = await uc.execute()

    assert result == COUNTRY_LIST
    mock_uow.countries.get_active_countries.assert_called_once()
    mock_cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache set failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_survives_cache_set_failure(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute()

    assert result == COUNTRY_LIST
    mock_uow.countries.get_active_countries.assert_called_once()


# ---------------------------------------------------------------------------
# Empty list → no cache
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_does_not_cache_empty_list(uc, mock_uow, mock_cache):
    mock_cache.get_json.return_value = None
    mock_uow.countries.get_active_countries.return_value = []

    result = await uc.execute()

    assert result == []
    mock_cache.set_json.assert_not_awaited()
