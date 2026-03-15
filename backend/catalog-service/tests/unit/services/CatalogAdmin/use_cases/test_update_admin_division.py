import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions.catalog_admin import AdminDivisionNotFoundError, AdminDivisionConflictError
from app.services.catalog_admin.schemas.admin_division import UpdateAdminDivisionRequest, AdminDivisionResponse
from app.services.catalog_admin.use_cases.update_admin_division import UpdateAdminDivisionUseCase

COUNTRY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_DIVISION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

REQUEST = UpdateAdminDivisionRequest(name="Cundinamarca Actualizado", is_active=True)


def _make_db_admin_division():
    m = MagicMock()
    m.id = ADMIN_DIVISION_ID
    m.country_id = COUNTRY_ID
    m.code = "CUN"
    m.iso_code = "CO-CUN"
    m.name = "Cundinamarca Actualizado"
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
    return UpdateAdminDivisionUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_admin_division.run_in_threadpool")
async def test_updates_admin_division_caches_fresh_data(mock_run, uc, mock_uow, mock_cache):
    admin_division = _make_db_admin_division()
    mock_run.return_value = admin_division

    result = await uc.execute(admin_division_id=ADMIN_DIVISION_ID, request=REQUEST)

    assert isinstance(result, AdminDivisionResponse)
    mock_uow.commit.assert_awaited_once()
    mock_uow.refresh.assert_awaited_once_with(admin_division)
    mock_cache.set_json.assert_awaited_once()


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_admin_division.run_in_threadpool")
async def test_raises_not_found_when_admin_division_missing(mock_run, uc, mock_uow):
    mock_run.return_value = None

    with pytest.raises(AdminDivisionNotFoundError):
        await uc.execute(admin_division_id=ADMIN_DIVISION_ID, request=REQUEST)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_admin_division.translate_db_error")
@patch("app.services.catalog_admin.use_cases.update_admin_division.run_in_threadpool")
async def test_rolls_back_and_raises_on_db_error(mock_run, mock_translate, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_admin_division()
    mock_uow.commit.side_effect = Exception("unique constraint")
    mock_translate.return_value = AdminDivisionConflictError(field="name", value="Cundinamarca Actualizado")

    with pytest.raises(AdminDivisionConflictError):
        await uc.execute(admin_division_id=ADMIN_DIVISION_ID, request=REQUEST)

    mock_uow.rollback.assert_awaited_once()
    mock_cache.set_json.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cache failure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.catalog_admin.use_cases.update_admin_division.run_in_threadpool")
async def test_survives_cache_failure(mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_db_admin_division()
    mock_cache.set_json.side_effect = Exception("Redis down")

    result = await uc.execute(admin_division_id=ADMIN_DIVISION_ID, request=REQUEST)

    assert isinstance(result, AdminDivisionResponse)
    mock_uow.commit.assert_awaited_once()
