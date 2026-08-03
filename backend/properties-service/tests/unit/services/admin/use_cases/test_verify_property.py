import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.core.exceptions.listing import (
    InvalidStatusTransitionError,
    PropertyNotFoundError,
    SetVisibilityError,
)
from app.models.listing import VerificationStatus
from app.schemas.principal import Principal
from app.services.admin.schemas.admin_schemas import VerifyPropertyRequest
from app.services.admin.use_cases.moderation.verify import VerifyPropertyUseCase
from app.services.shared.helpers.cache_keys import cache_property, client_properties, map_h3_cell

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
# Distinto del owner a propósito: la firma de moderación es del admin, y con el
# mismo uuid los asserts de `verified_by` pasarían por accidente.
ADMIN_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN = Principal(sub=ADMIN_ID)

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

@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_transitions_unverified_to_pending(mock_run, uc, mock_uow, mock_cache):
    prop = _make_mock_prop(VerificationStatus.unverified)
    mock_run.return_value = prop
    request = VerifyPropertyRequest(verification_status=VerificationStatus.pending)

    await uc.execute(principal=ADMIN, property_id=PROP_ID, request=request)

    assert prop.verification_status == VerificationStatus.pending
    mock_uow.commit.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_transitions_pending_to_verified(mock_run, uc, mock_uow):
    prop = _make_mock_prop(VerificationStatus.pending)
    mock_run.return_value = prop
    request = VerifyPropertyRequest(verification_status=VerificationStatus.verified)

    await uc.execute(principal=ADMIN, property_id=PROP_ID, request=request)

    assert prop.verification_status == VerificationStatus.verified


@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_transitions_pending_to_rejected_with_reason(mock_run, uc, mock_uow):
    prop = _make_mock_prop(VerificationStatus.pending)
    mock_run.return_value = prop
    request = VerifyPropertyRequest(
        verification_status=VerificationStatus.rejected,
        rejection_reason="Missing documents",
    )

    await uc.execute(principal=ADMIN, property_id=PROP_ID, request=request)

    assert prop.verification_status == VerificationStatus.rejected
    assert prop.rejection_reason == "Missing documents"


@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_transitions_rejected_back_to_pending(mock_run, uc, mock_uow):
    prop = _make_mock_prop(VerificationStatus.rejected)
    mock_run.return_value = prop
    request = VerifyPropertyRequest(verification_status=VerificationStatus.pending)

    await uc.execute(principal=ADMIN, property_id=PROP_ID, request=request)

    assert prop.verification_status == VerificationStatus.pending


# ---------------------------------------------------------------------------
# Cache includes H3 keys
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_invalidates_property_user_and_h3_cache_keys(mock_run, uc, mock_cache):
    prop = _make_mock_prop(VerificationStatus.unverified)
    mock_run.return_value = prop

    await uc.execute(
        principal=ADMIN,
        property_id=PROP_ID,
        request=VerifyPropertyRequest(verification_status=VerificationStatus.pending),
    )

    deleted_keys = mock_cache.delete.call_args.kwargs["key"]
    assert cache_property(property_id=PROP_ID) in deleted_keys
    assert client_properties(user_id=OWNER_ID) in deleted_keys
    assert map_h3_cell(H3_R9) in deleted_keys
    assert map_h3_cell(H3_R7) in deleted_keys


# ---------------------------------------------------------------------------
# `verified` ya no es terminal — sale a `pending` y a `rejected`
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "target, reason",
    [
        (VerificationStatus.pending, None),
        (VerificationStatus.rejected, "fotos no corresponden al inmueble"),
    ],
)
@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_allows_exit_from_verified(mock_run, uc, mock_uow, target, reason):
    """Una property aprobada que después viola las normas tiene que poder volver
    a la cola (`pending`) o perder el sello (`rejected`)."""
    prop = _make_mock_prop(VerificationStatus.verified)
    mock_run.return_value = prop

    await uc.execute(
        principal=ADMIN,
        property_id=PROP_ID,
        request=VerifyPropertyRequest(
            verification_status = target,
            rejection_reason = reason,
        ),
    )

    assert prop.verification_status == target
    mock_uow.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Firma de quién moderó
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "target, reason",
    [
        (VerificationStatus.verified, None),
        (VerificationStatus.rejected, "documentos ilegibles"),
    ],
)
@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_signs_who_resolved_the_verification(mock_run, uc, target, reason):
    """Aprobar y rechazar son las dos formas de *resolver*, y las dos se firman."""
    prop = _make_mock_prop(VerificationStatus.pending)
    mock_run.return_value = prop

    await uc.execute(
        principal = ADMIN,
        property_id = PROP_ID,
        request = VerifyPropertyRequest(
            verification_status = target,
            rejection_reason = reason,
        ),
    )

    assert prop.verified_by == ADMIN_ID
    assert prop.updated_by == ADMIN_ID


@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_requeueing_clears_the_signature(mock_run, uc):
    """Volver a la cola invalida la resolución anterior: si la firma quedara, el
    panel mostraría un aprobador para algo que está sin resolver."""
    prop = _make_mock_prop(VerificationStatus.verified)
    prop.verified_by = uuid.uuid4()
    mock_run.return_value = prop

    await uc.execute(
        principal = ADMIN,
        property_id = PROP_ID,
        request = VerifyPropertyRequest(verification_status=VerificationStatus.pending),
    )

    assert prop.verified_by is None
    assert prop.updated_by == ADMIN_ID


# ---------------------------------------------------------------------------
# El motivo solo viaja con el rechazo (validado en el schema, no en el UC)
# ---------------------------------------------------------------------------

def test_rejecting_without_reason_is_rejected_by_schema():
    with pytest.raises(ValidationError):
        VerifyPropertyRequest(verification_status=VerificationStatus.rejected)


@pytest.mark.parametrize(
    "target",
    [VerificationStatus.verified, VerificationStatus.pending],
)
def test_reason_is_rejected_by_schema_when_not_rejecting(target):
    with pytest.raises(ValidationError):
        VerifyPropertyRequest(
            verification_status = target,
            rejection_reason = "fotos no corresponden al inmueble",
        )


def test_blank_reason_does_not_count_as_a_reason():
    """`StrictBase` hace `str_strip_whitespace`, así que "   " llega como "" —
    y un motivo vacío deja al dueño igual de a ciegas que no mandar ninguno."""
    with pytest.raises(ValidationError):
        VerifyPropertyRequest(
            verification_status = VerificationStatus.rejected,
            rejection_reason = "   ",
        )


# ---------------------------------------------------------------------------
# Invalid transition — nadie vuelve a `unverified`
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_raises_invalid_transition_back_to_unverified(mock_run, uc, mock_uow):
    mock_run.return_value = _make_mock_prop(VerificationStatus.verified)
    request = VerifyPropertyRequest(verification_status=VerificationStatus.unverified)

    with pytest.raises(InvalidStatusTransitionError):
        await uc.execute(principal=ADMIN, property_id=PROP_ID, request=request)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_raises_not_found_when_property_missing(mock_run, uc, mock_uow):
    mock_run.return_value = None

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(
            principal=ADMIN,
            property_id=PROP_ID,
            request=VerifyPropertyRequest(verification_status=VerificationStatus.pending),
        )

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_rolls_back_and_raises_set_visibility_error_on_commit_failure(mock_run, uc, mock_uow):
    mock_run.return_value = _make_mock_prop(VerificationStatus.unverified)
    mock_uow.commit.side_effect = Exception("db error")

    with pytest.raises(SetVisibilityError):
        await uc.execute(
            principal=ADMIN,
            property_id=PROP_ID,
            request=VerifyPropertyRequest(verification_status=VerificationStatus.pending),
        )

    mock_uow.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.admin.use_cases.moderation.verify.run_in_threadpool")
async def test_survives_cache_delete_failure(mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = _make_mock_prop(VerificationStatus.unverified)
    mock_cache.delete.side_effect = Exception("Redis down")

    await uc.execute(
        principal=ADMIN,
        property_id=PROP_ID,
        request=VerifyPropertyRequest(verification_status=VerificationStatus.pending),
    )

    mock_uow.commit.assert_awaited_once()
