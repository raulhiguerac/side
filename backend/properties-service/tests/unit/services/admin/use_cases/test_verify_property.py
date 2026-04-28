import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import (
    InvalidStatusTransitionError,
    PropertyNotFoundError,
    SetVisibilityError,
)
from app.models.property import VerificationStatus
from app.schemas.principal import Principal
from app.services.admin.schemas.admin_schemas import VerifyPropertyRequest
from app.services.admin.use_cases.verify_property import VerifyPropertyUseCase
from app.services.shared.helpers.cache_keys import cache_property, client_properties, map_h3_cell

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

H3_R9 = "8fb5a30a2dfffff"
H3_R7 = "87b5a30a2ffffff"


def _make_mock_prop(verification_status: VerificationStatus):
    m = MagicMock()
    m.id = PROP_ID
    m.owner_id = OWNER_ID
    m.verification_status = verification_status
    m.h3_r9 = H3_R9
    m.h3_r7 = H3_R7
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(mock_uow, mock_cache):
    return VerifyPropertyUseCase(uow=mock_uow, cache=mock_cache)


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_transitions_unverified_to_pending(mock_run, uc, mock_uow, mock_cache):
    prop = _make_mock_prop(VerificationStatus.unverified)
    mock_run.return_value = prop
    request = VerifyPropertyRequest(verification_status=VerificationStatus.pending)

    await uc.execute(property_id=PROP_ID, request=request)

    assert prop.verification_status == VerificationStatus.pending
    mock_uow.commit.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_transitions_pending_to_verified(mock_run, uc, mock_uow):
    prop = _make_mock_prop(VerificationStatus.pending)
    mock_run.return_value = prop
    request = VerifyPropertyRequest(verification_status=VerificationStatus.verified)

    await uc.execute(property_id=PROP_ID, request=request)

    assert prop.verification_status == VerificationStatus.verified


@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_transitions_pending_to_rejected_with_reason(mock_run, uc, mock_uow):
    prop = _make_mock_prop(VerificationStatus.pending)
    mock_run.return_value = prop
    request = VerifyPropertyRequest(
        verification_status=VerificationStatus.rejected,
        rejection_reason="Missing documents",
    )

    await uc.execute(property_id=PROP_ID, request=request)

    assert prop.verification_status == VerificationStatus.rejected
    assert prop.rejection_reason == "Missing documents"


@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_transitions_rejected_back_to_pending(mock_run, uc, mock_uow):
    prop = _make_mock_prop(VerificationStatus.rejected)
    mock_run.return_value = prop
    request = VerifyPropertyRequest(verification_status=VerificationStatus.pending)

    await uc.execute(property_id=PROP_ID, request=request)

    assert prop.verification_status == VerificationStatus.pending


# ---------------------------------------------------------------------------
# Cache includes H3 keys
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_invalidates_property_user_and_h3_cache_keys(mock_run, uc, mock_cache):
    prop = _make_mock_prop(VerificationStatus.unverified)
    mock_run.return_value = prop

    await uc.execute(
        property_id=PROP_ID,
        request=VerifyPropertyRequest(verification_status=VerificationStatus.pending),
    )

    deleted_keys = mock_cache.delete.call_args.kwargs["key"]
    assert cache_property(property_id=PROP_ID) in deleted_keys
    assert client_properties(user_id=OWNER_ID) in deleted_keys
    assert map_h3_cell(H3_R9) in deleted_keys
    assert map_h3_cell(H3_R7) in deleted_keys


# ---------------------------------------------------------------------------
# Invalid transition — verified has no allowed next states
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_raises_invalid_transition_from_verified(mock_run, uc, mock_uow):
    mock_run.return_value = _make_mock_prop(VerificationStatus.verified)
    request = VerifyPropertyRequest(verification_status=VerificationStatus.pending)

    with pytest.raises(InvalidStatusTransitionError):
        await uc.execute(property_id=PROP_ID, request=request)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_raises_not_found_when_property_missing(mock_run, uc, mock_uow):
    mock_run.return_value = None

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(
            property_id=PROP_ID,
            request=VerifyPropertyRequest(verification_status=VerificationStatus.pending),
        )

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_rolls_back_and_raises_set_visibility_error_on_commit_failure(mock_run, uc, mock_uow):
    mock_run.return_value = _make_mock_prop(VerificationStatus.unverified)
    mock_uow.commit.side_effect = Exception("db error")

    with pytest.raises(SetVisibilityError):
        await uc.execute(
            property_id=PROP_ID,
            request=VerifyPropertyRequest(verification_status=VerificationStatus.pending),
        )

    mock_uow.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.verify_property.run_in_threadpool")
async def test_survives_cache_delete_failure(mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_mock_prop(VerificationStatus.unverified)
    mock_cache.delete.side_effect = Exception("Redis down")

    await uc.execute(
        property_id=PROP_ID,
        request=VerifyPropertyRequest(verification_status=VerificationStatus.pending),
    )

    mock_uow.commit.assert_awaited_once()
