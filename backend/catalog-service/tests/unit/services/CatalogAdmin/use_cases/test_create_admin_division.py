import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions.catalog_admin import AdminDivisionConflictError
from app.services.catalog_admin.schemas.admin_division import CreateAdminDivisionRequest, AdminDivisionResponse
from app.services.catalog_admin.use_cases.create_admin_division import CreateAdminDivisionUseCase

COUNTRY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_DIVISION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

REQUEST = CreateAdminDivisionRequest(
    country_id=COUNTRY_ID,
    code="CUN",
    iso_code="CO-CUN",
    name="Cundinamarca",
    type_name="department",
)


def _make_db_admin_division():
    m = MagicMock()
    m.id = ADMIN_DIVISION_ID
    m.country_id = COUNTRY_ID
    m.code = "CUN"
    m.iso_code = "CO-CUN"
    m.name = "Cundinamarca"
    m.type_name = "department"
    m.is_active = True
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
    return CreateAdminDivisionUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_admin_division.run_in_threadpool")
async def test_creates_admin_division_and_caches(mock_run, uc, mock_uow, mock_cache):
    admin_division = _make_db_admin_division()
    mock_run.return_value = admin_division

    result = await uc.execute(request=REQUEST)

    assert isinstance(result, AdminDivisionResponse)
    assert result.name == "Cundinamarca"
    mock_uow.commit.assert_awaited_once()
    mock_uow.refresh.assert_awaited_once_with(admin_division)
    mock_cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_admin_division.translate_db_error")
@patch("app.services.catalog_admin.use_cases.create_admin_division.run_in_threadpool")
async def test_rolls_back_and_raises_on_db_error(mock_run, mock_translate, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_admin_division()
    mock_uow.commit.side_effect = Exception("unique constraint")
    mock_translate.return_value = AdminDivisionConflictError(field="code", value="CUN")

    with pytest.raises(AdminDivisionConflictError):
        await uc.execute(request=REQUEST)

    mock_uow.rollback.assert_awaited_once()
    mock_cache.set_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.create_admin_division.run_in_threadpool")
async def test_survives_cache_failure(mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_admin_division()
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute(request=REQUEST)

    assert isinstance(result, AdminDivisionResponse)
    mock_uow.commit.assert_awaited_once()
