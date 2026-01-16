import os

from keycloak import KeycloakOpenID

from app.core.exceptions.identity_provider import (
    IdentityProviderMisconfiguredError,
)
from app.core.logging.logger import get_logger
from app.integrations.identity_provider.keycloak.mappers.error_mapper import (
    translate_keycloak_error,
)

logger = get_logger(__name__)

class KeycloakAuthClient:
    def __init__(self):
        server_url = os.getenv('KEYCLOAK_URL')
        client_id = os.getenv('KC_CLIENT_AUTH')
        realm_name = os.getenv('KC_REALM')
        client_secret_key = os.getenv('KC_AUTH_SECRET')

        missing = [
            name for name, value in {
                "KEYCLOAK_URL": server_url,
                "KC_CLIENT_AUTH": client_id,
                "KC_REALM": realm_name,
                "KC_AUTH_SECRET": client_secret_key,
            }.items()
            if not value
        ]

        if missing:
            raise IdentityProviderMisconfiguredError(
                detail=f"Missing Keycloak env vars: {', '.join(missing)}"
            )
        
        self.auth_client = KeycloakOpenID(
            server_url = server_url,
            client_id = client_id,
            realm_name = realm_name,
            client_secret_key = client_secret_key,
            verify = True
        )
    
    def keycloak_login(self, email: str, password: str) -> dict:
        try:
            return self.auth_client.token(
                username = email,
                password = password
            )

        except Exception as e:
            translate_keycloak_error(error=e, operation="login")
        
    def keycloak_refresh_token(self, refresh_token: str) -> dict:
        try:
            return self.auth_client.refresh_token(refresh_token=refresh_token)
        
        except Exception as e:
            translate_keycloak_error(error=e, operation="refresh")
    
    def keycloak_revoke_token(self, refresh_token: str) -> None:
        try:
            return self.auth_client.logout(refresh_token=refresh_token)
        
        except Exception as e:
            translate_keycloak_error(error=e, operation="revoke")
