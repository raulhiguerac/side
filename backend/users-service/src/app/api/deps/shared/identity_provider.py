from functools import lru_cache

from app.integrations.identity_provider.keycloak.admin_client import KeycloakAdminClient
from app.integrations.identity_provider.keycloak.auth_client import KeycloakAuthClient
from app.services.auth.adapters.keycloak_auth_provider import (
    KeycloakAuthenticationProvider,
)
from app.services.auth.adapters.keycloak_idp import KeycloakIdentityProvider
from app.services.auth.ports.authentication_provider import AuthenticationProvider
from app.services.auth.ports.identity_provider import IdentityProvider


@lru_cache(maxsize=1)
def get_identity_provider() -> IdentityProvider:
    """Identity provider (Keycloak Admin API)."""
    return KeycloakIdentityProvider(client=KeycloakAdminClient())


@lru_cache(maxsize=1)
def get_auth_provider() -> AuthenticationProvider:
    """Authentication provider (Keycloak OIDC)."""
    return KeycloakAuthenticationProvider(client=KeycloakAuthClient())
