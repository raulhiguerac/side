from fastapi import Depends
from sqlmodel import Session

from app.api.deps.shared.cache import get_cache_port
from app.api.deps.shared.db import get_session
from app.api.deps.shared.email import get_email_sender
from app.api.deps.shared.identity_provider import (
    get_auth_provider,
    get_identity_provider,
)
from app.services.auth.adapters.sql_unit_of_work import SqlAuthUnitOfWork
from app.services.auth.helpers.profile_factory import ProfileFactory
from app.services.auth.ports.authentication_provider import AuthenticationProvider
from app.services.auth.ports.identity_provider import IdentityProvider
from app.services.auth.ports.unit_of_work import AuthUnitOfWork
from app.services.auth.services.reset_password_mailer import ResetPasswordMailer
from app.services.auth.use_cases.authenticate_account import AuthenticateAccountUseCase
from app.services.auth.use_cases.change_password import ChangeAccountPasswordUseCase
from app.services.auth.use_cases.confirm_reset_password import (
    ConfirmResetPasswordUseCase,
)
from app.services.auth.use_cases.logout import LogoutUseCase
from app.services.auth.use_cases.register_account import RegisterAccountUseCase
from app.services.auth.use_cases.request_reset_password import (
    RequestResetPasswordUseCase,
)
from app.services.shared.db.db_error_translator import DbErrorTranslator
from app.services.shared.policies.account_email_availability_policy import (
    AccountEmailAvailabilityPolicy,
)
from app.services.shared.policies.active_account_policy import AccountActivePolicy
from app.services.shared.ports.cache import CachePort
from app.services.shared.ports.email_sender import EmailSenderPort

# -----------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -----------------------------------------------------------------------------

def get_uow(session: Session = Depends(get_session)) -> AuthUnitOfWork:
    """One Unit of Work per request, bound to the current DB session."""
    return SqlAuthUnitOfWork(session=session)


# -----------------------------------------------------------------------------
# Policies / Guards (request-scoped)
# -----------------------------------------------------------------------------

def get_account_active_policy(
    uow: AuthUnitOfWork = Depends(get_uow),
) -> AccountActivePolicy:
    """Ensures an account exists and is active."""
    return AccountActivePolicy(uow=uow)


def get_email_availability_policy(
    uow: AuthUnitOfWork = Depends(get_uow),
) -> AccountEmailAvailabilityPolicy:
    """Ensures an email is available (e.g., for register)."""
    return AccountEmailAvailabilityPolicy(uow=uow)


# -----------------------------------------------------------------------------
# Mailers (request-scoped)
# -----------------------------------------------------------------------------

def get_reset_password_mailer(
    email_sender: EmailSenderPort = Depends(get_email_sender),
) -> ResetPasswordMailer:
    return ResetPasswordMailer(email_sender=email_sender)


# -----------------------------------------------------------------------------
# Use cases
# -----------------------------------------------------------------------------

def get_register_account_uc(
    uow: AuthUnitOfWork = Depends(get_uow),
    identity_provider: IdentityProvider = Depends(get_identity_provider),
    email_policy: AccountEmailAvailabilityPolicy = Depends(get_email_availability_policy),
) -> RegisterAccountUseCase:
    """Register an account (DB + IDP provisioning)."""
    return RegisterAccountUseCase(
        uow=uow,
        idp=identity_provider,
        email_policy=email_policy,
        profile_factory=ProfileFactory(),
        db_errors=DbErrorTranslator(),
    )


def get_authenticate_account_uc(
    auth_provider: AuthenticationProvider = Depends(get_auth_provider),
    account_policy: AccountActivePolicy = Depends(get_account_active_policy),
) -> AuthenticateAccountUseCase:
    """Authenticate accounts (login / refresh)."""
    return AuthenticateAccountUseCase(
        auth_provider=auth_provider,
        account_guard=account_policy,
    )


def get_change_password_uc(
    auth_provider: AuthenticationProvider = Depends(get_auth_provider),
    identity_provider: IdentityProvider = Depends(get_identity_provider),
    account_policy: AccountActivePolicy = Depends(get_account_active_policy),
) -> ChangeAccountPasswordUseCase:
    return ChangeAccountPasswordUseCase(
        auth_provider=auth_provider,
        idp=identity_provider,
        account_policy=account_policy,
    )


def get_logout_account_uc(
    auth_provider: AuthenticationProvider = Depends(get_auth_provider),
) -> LogoutUseCase:
    return LogoutUseCase(auth_provider=auth_provider)


def get_reset_password_uc(
    uow: AuthUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
    reset_password_mailer: ResetPasswordMailer = Depends(get_reset_password_mailer),
) -> RequestResetPasswordUseCase:
    return RequestResetPasswordUseCase(
        uow=uow,
        cache_client=cache,
        reset_password_mailer=reset_password_mailer,
    )

def get_confirm_reset_password_uc(
    uow: AuthUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
    identity_provider: IdentityProvider = Depends(get_identity_provider),
) -> ConfirmResetPasswordUseCase:
    return ConfirmResetPasswordUseCase(
        uow=uow,
        cache_client=cache,
        idp=identity_provider,
    )