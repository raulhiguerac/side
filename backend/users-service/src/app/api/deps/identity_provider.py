from functools import lru_cache
from app.integrations.identity_provider.keycloak.admin_client import KeycloakAdminClient
from app.services.auth.adapters.keycloak_idp import KeycloakIdentityProvider

@lru_cache
def get_idp() -> KeycloakIdentityProvider:
    return KeycloakIdentityProvider(KeycloakAdminClient())
