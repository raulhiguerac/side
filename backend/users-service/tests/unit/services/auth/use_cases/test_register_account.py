import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import TypeAdapter
from sqlalchemy.exc import IntegrityError

from app.core.exceptions.auth import EmailAlreadyRegisteredError
from app.core.exceptions.base import BaseError
from app.models.account import Account, OnboardingStep
from app.services.auth.schemas.registration import RegisterRequest
from app.services.auth.use_cases.register_account import RegisterAccountUseCase


REGISTER_DATA = [
    {
        "first_name": "pepito",
        "last_name": "perez",
        "email": "pepito@micasaenminutos.com",
        "password": "fakepassword",
        "phone": "1234567890",
        "account_type": "person",
    },
    {
        "display_name": "inmobiliaria fake",
        "email": "inmobiliaria@micasaenminutos.com",
        "password": "fakepassword",
        "phone": "1234567890",
        "account_type": "organization",
    },
]

REGISTER_ADAPTER = TypeAdapter(RegisterRequest)
REGISTER_REQUESTS = [REGISTER_ADAPTER.validate_python(d) for d in REGISTER_DATA]


# ----------------------------
# Fixtures
# ----------------------------

@pytest.fixture
def uow():
    uow = AsyncMock()
    # asegura que existan estos sub-atributos async
    uow.accounts = AsyncMock()
    uow.profiles = AsyncMock()
    uow.compensation_tasks = AsyncMock()
    return uow

@pytest.fixture
def idp():
    return AsyncMock()

@pytest.fixture
def email_policy():
    return AsyncMock()

@pytest.fixture
def profile_factory():
    return MagicMock()

@pytest.fixture
def db_errors():
    return MagicMock()

@pytest.fixture
def uc(uow, idp, email_policy, profile_factory, db_errors):
    uc = RegisterAccountUseCase(
        uow=uow,
        idp=idp,
        email_policy=email_policy,
        profile_factory=profile_factory,
        db_errors=db_errors,
    )
    # mock del método privado para no depender del detalle de implementación
    uc._enqueue_delete_kc_user_task = AsyncMock(return_value=None)
    return uc


# ----------------------------
# Happy path
# ----------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("req", REGISTER_REQUESTS)
async def test_register_success(uc, req, uow, idp, email_policy, profile_factory):
    kc_user_id = uuid.uuid4()
    fake_profile = object()

    email_policy.ensure_email_available.return_value = None
    idp.create_account.return_value = kc_user_id
    uow.accounts.create_account.return_value = None
    profile_factory.from_register.return_value = fake_profile
    uow.profiles.create_profile.return_value = None
    uow.commit.return_value = None

    result = await uc.register(req=req)

    assert isinstance(result, Account)
    assert result.account_id == kc_user_id
    assert result.email == req.email
    assert result.account_type == req.account_type
    assert result.onboarding_step == OnboardingStep.intent

    email_policy.ensure_email_available.assert_awaited_once_with(email=req.email)
    idp.create_account.assert_awaited_once_with(email=req.email, password=req.password)

    uow.accounts.create_account.assert_awaited_once()
    created_account = uow.accounts.create_account.await_args.kwargs["account"]
    assert isinstance(created_account, Account)
    assert created_account.account_id == kc_user_id
    assert created_account.email == req.email
    assert created_account.account_type == req.account_type
    assert created_account.onboarding_step == OnboardingStep.intent

    profile_factory.from_register.assert_called_once_with(req=req, account_id=kc_user_id)
    uow.profiles.create_profile.assert_awaited_once_with(profile=fake_profile)

    uow.commit.assert_awaited_once()
    uow.rollback.assert_not_called()
    uc._enqueue_delete_kc_user_task.assert_not_called()
    uow.compensation_tasks.add.assert_not_called()


# ----------------------------
# Email not available -> short-circuit
# ----------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("req", REGISTER_REQUESTS)
async def test_register_fails_when_email_not_available(
    uc, req, uow, idp, email_policy, profile_factory
):
    email_policy.ensure_email_available.side_effect = EmailAlreadyRegisteredError(email=req.email)

    with pytest.raises(EmailAlreadyRegisteredError):
        await uc.register(req=req)

    email_policy.ensure_email_available.assert_awaited_once_with(email=req.email)

    idp.create_account.assert_not_called()
    uow.accounts.create_account.assert_not_called()
    uow.profiles.create_profile.assert_not_called()
    profile_factory.from_register.assert_not_called()

    uow.commit.assert_not_called()
    uow.rollback.assert_not_called()
    uc._enqueue_delete_kc_user_task.assert_not_called()
    uow.compensation_tasks.add.assert_not_called()


# ----------------------------
# IDP create fails -> Exception branch -> BaseError(REGISTER_FAILED) + enqueue
# ----------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("req", REGISTER_REQUESTS)
async def test_register_when_idp_create_fails_raises_register_failed_and_enqueues(
    uc, req, uow, idp, email_policy
):
    email_policy.ensure_email_available.return_value = None
    idp.create_account.side_effect = Exception("Keycloak unreachable")

    with pytest.raises(BaseError) as exc_info:
        await uc.register(req=req)

    assert exc_info.value.code == "REGISTER_FAILED"

    email_policy.ensure_email_available.assert_awaited_once_with(email=req.email)
    idp.create_account.assert_awaited_once_with(email=req.email, password=req.password)

    uow.rollback.assert_awaited_once()
    uc._enqueue_delete_kc_user_task.assert_awaited_once()
    uow.compensation_tasks.add.assert_not_called()


# ----------------------------
# IntegrityError + delete KC success -> raises translated error, no enqueue
# ----------------------------

@pytest.mark.asyncio
async def test_register_integrity_error_deletes_kc_success_no_enqueue(
    uc, uow, idp, email_policy, db_errors
):
    req = REGISTER_REQUESTS[0]
    kc_user_id = uuid.uuid4()

    email_policy.ensure_email_available.return_value = None
    idp.create_account.return_value = kc_user_id
    uow.accounts.create_account.side_effect = IntegrityError("stmt", "params", Exception("dup"))

    translated = EmailAlreadyRegisteredError(email=req.email)
    db_errors.translate_integrity_error.return_value = translated

    with pytest.raises(EmailAlreadyRegisteredError):
        await uc.register(req=req)

    uow.rollback.assert_awaited_once()
    idp.delete_account.assert_awaited_once_with(kc_user_id)

    uc._enqueue_delete_kc_user_task.assert_not_called()
    uow.compensation_tasks.add.assert_not_called()


# ----------------------------
# IntegrityError + delete KC fails -> enqueue + raises translated error
# ----------------------------

@pytest.mark.asyncio
async def test_register_integrity_error_delete_kc_fails_enqueues_then_raises(
    uc, uow, idp, email_policy, db_errors
):
    req = REGISTER_REQUESTS[0]
    kc_user_id = uuid.uuid4()

    email_policy.ensure_email_available.return_value = None
    idp.create_account.return_value = kc_user_id
    uow.accounts.create_account.side_effect = IntegrityError("stmt", "params", Exception("dup"))

    idp.delete_account.side_effect = Exception("KC unreachable")

    translated = EmailAlreadyRegisteredError(email=req.email)
    db_errors.translate_integrity_error.return_value = translated

    with pytest.raises(EmailAlreadyRegisteredError):
        await uc.register(req=req)

    uow.rollback.assert_awaited_once()
    idp.delete_account.assert_awaited_once_with(kc_user_id)
    uc._enqueue_delete_kc_user_task.assert_awaited_once()
    uow.compensation_tasks.add.assert_not_called()


# ----------------------------
# BaseError from DB layer -> rollback + enqueue + re-raise same error
# ----------------------------

@pytest.mark.asyncio
async def test_register_base_error_rolls_back_enqueues_and_reraises(
    uc, uow, idp, email_policy
):
    req = REGISTER_REQUESTS[0]
    kc_user_id = uuid.uuid4()

    email_policy.ensure_email_available.return_value = None
    idp.create_account.return_value = kc_user_id

    domain_err = BaseError(message="Some domain error", code="DOMAIN_ERROR")
    uow.accounts.create_account.side_effect = domain_err

    with pytest.raises(BaseError) as exc_info:
        await uc.register(req=req)

    assert exc_info.value is domain_err

    uow.rollback.assert_awaited_once()
    uc._enqueue_delete_kc_user_task.assert_awaited_once()
    uow.compensation_tasks.add.assert_not_called()
