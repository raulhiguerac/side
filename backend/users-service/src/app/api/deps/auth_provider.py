from functools import lru_cache

from app.integrations.identity_provider.keycloak.auth_client import KeycloakAuthClient
from app.services.auth.adapters.keycloak_auth_provider import KeycloakAuthenticationProvider

@lru_cache
def get_auth_provider() -> KeycloakAuthenticationProvider:
    return KeycloakAuthenticationProvider(
        KeycloakAuthClient()
    )
