from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.services.auth.ports.unit_of_work import AuthUnitOfWork
from app.services.auth.adapters.sql_unit_of_work import SqlAuthUnitOfWork

from app.services.shared.policies.active_account_policy import AccountActivePolicy
from app.services.shared.policies.account_email_availability_policy import (
    AccountEmailAvailabilityPolicy,
)

from app.services.auth.use_cases.register_account import RegisterAccountUseCase
from app.services.auth.use_cases.authenticate_account import AuthenticateAccountUseCase
from app.services.auth.use_cases.change_password import ChangeAccountPasswordUseCase
from app.services.auth.use_cases.logout import LogoutUseCase

from app.services.auth.ports.identity_provider import IdentityProvider
from app.services.auth.ports.authentication_provider import AuthenticationProvider

from app.integrations.identity_provider.keycloak.auth_client import KeycloakAuthClient
from app.integrations.identity_provider.keycloak.admin_client import KeycloakAdminClient

from app.services.auth.adapters.keycloak_auth_provider import KeycloakAuthenticationProvider
from app.services.auth.adapters.keycloak_idp import KeycloakIdentityProvider

from app.services.auth.helpers.profile_factory import ProfileFactory
from app.services.auth.helpers.db_error_translator import DbErrorTranslator


# -------------------------------------------------------------------------
# Providers (stateless → safe to cache)
# -------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_identity_provider() -> IdentityProvider:
    """
    Identity provider (Keycloak Admin API).
    Cached because it is stateless and safe to reuse.
    """
    return KeycloakIdentityProvider(client=KeycloakAdminClient())


@lru_cache(maxsize=1)
def get_auth_provider() -> AuthenticationProvider:
    """
    Authentication provider (Keycloak OIDC).
    Cached because it is stateless and safe to reuse.
    """
    return KeycloakAuthenticationProvider(client=KeycloakAuthClient())


# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------

def get_uow(session: Session = Depends(get_session)) -> AuthUnitOfWork:
    """
    One Unit of Work per request, bound to the current DB session.
    """
    return SqlAuthUnitOfWork(session=session)



# -------------------------------------------------------------------------
# Policies / Guards (request-scoped)
# -------------------------------------------------------------------------

def get_account_active_policy(
    uow: AuthUnitOfWork = Depends(get_uow),
) -> AccountActivePolicy:
    """
    Ensures an account exists and is active (e.g., for login/change password).
    """
    return AccountActivePolicy(uow=uow)


def get_email_availability_policy(
    uow: AuthUnitOfWork = Depends(get_uow),
) -> AccountEmailAvailabilityPolicy:
    """
    Ensures an email is available (e.g., for register).
    """
    return AccountEmailAvailabilityPolicy(uow=uow)


# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def get_register_account_uc(
    uow: AuthUnitOfWork = Depends(get_uow),
    identity_provider: IdentityProvider = Depends(get_identity_provider),
    email_policy: AccountEmailAvailabilityPolicy = Depends(get_email_availability_policy),
) -> RegisterAccountUseCase:
    """
    Use case for registering an account (DB + IDP provisioning).
    """
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
    """
    Use case for authenticating accounts (login / refresh).
    """
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
    return LogoutUseCase(
        auth_provider=auth_provider,
    )