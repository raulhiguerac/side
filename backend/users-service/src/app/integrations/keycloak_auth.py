import os
from dotenv import load_dotenv
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError

from app.core.exceptions.integrations import IdentityProviderUnavailableError
from app.core.exceptions.auth import InvalidCredentialsError

from app.integrations._utils import get_keycloak_status,get_keycloak_error_text

from app.core.logging.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

class KeycloakAuthIntegration:
    def __init__(self):
        self.auth_client = KeycloakOpenID(
            server_url = os.getenv('KEYCLOAK_URL'),
            client_id = os.getenv('KC_CLIENT_AUTH'),
            realm_name = os.getenv('KC_REALM'),
            client_secret_key = os.getenv('KC_AUTH_SECRET'),
            verify = True
        )
    
    def keycloak_login(self, email: str, password: str) -> dict:
        try:
            return self.auth_client.token(
                username = email,
                password = password
            )

        except KeycloakAuthenticationError as e:
            raise InvalidCredentialsError(cause=e) from e

        except KeycloakPostError as e:
            status = get_keycloak_status(e)
            error_text = get_keycloak_error_text(e)

            if status in (400, 401) and "invalid_grant" in error_text:
                logger.warning(
                    "keycloak_login_failed",
                    extra={
                        "extra": {
                            "kc_status": status,
                            "kc_error": error_text[:200],
                        }
                    },
                )
                raise InvalidCredentialsError(cause=e) from e

            raise IdentityProviderUnavailableError(
                detail=error_text,
                cause=e
            ) from e

        except Exception as e:
            raise IdentityProviderUnavailableError(
                detail=error_text,
                cause=e
            ) from e
