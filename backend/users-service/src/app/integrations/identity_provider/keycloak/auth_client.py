import os
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError

from app.core.exceptions.identity_provider import IdentityProviderUnavailableError, IdentityProviderMisconfiguredError
from app.core.exceptions.auth import InvalidCredentialsError, InvalidRefreshTokenError
from app.core.exceptions.validation import BadRequestError

from app.integrations._utils import get_keycloak_status,get_keycloak_error_text

from app.core.logging.logger import get_logger

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

        except KeycloakAuthenticationError as e:
            text = str(e).lower()
            if "invalid_grant" in text or "invalid user credentials" in text:
                logger.warning(
                    "keycloak_login_invalid_credentials",
                    extra={"extra": {"kc_error": text[:200]}},
                )
                raise InvalidCredentialsError(cause=e) from e

            if "invalid_client" in text or "unauthorized_client" in text:
                logger.error(
                    "keycloak_login_client_misconfigured",
                    extra={"extra": {"kc_error": text[:200]}},
                )
                raise IdentityProviderMisconfiguredError(cause=e) from e

            logger.exception("keycloak_login_auth_error_unexpected")
            raise IdentityProviderUnavailableError(detail=str(e), cause=e) from e

        except KeycloakPostError as e:
            status = get_keycloak_status(e)
            text = (get_keycloak_error_text(e) or "").lower()

            match status:
                case 400 | 401:
                    if "invalid_grant" in text:
                        logger.warning(
                            "keycloak_login_invalid_credentials",
                            extra={"extra": {"kc_status": status, "kc_error": text[:200]}},
                        )
                        raise InvalidCredentialsError(cause=e) from e

                    if "invalid_client" in text or "unauthorized_client" in text:
                        logger.error(
                            "keycloak_login_client_misconfigured",
                            extra={"extra": {"kc_status": status, "kc_error": text[:200]}},
                        )
                        raise IdentityProviderMisconfiguredError(cause=e) from e

                    if "invalid_request" in text:
                        raise BadRequestError(detail=text, cause=e) from e

            raise IdentityProviderUnavailableError(detail=text, cause=e) from e

        except Exception as e:
            raise IdentityProviderUnavailableError(cause=e) from e
        
    def keycloak_refresh_token(self, refresh_token: str) -> dict:
        try:
            return self.auth_client.refresh_token(refresh_token=refresh_token)
        
        except KeycloakAuthenticationError as e:
            text = str(e).lower()
            if "invalid_grant" in text or "invalid user credentials" in text:
                logger.warning(
                    "keycloak_login_invalid_credentials",
                    extra={"extra": {"kc_error": text[:200]}},
                )
                raise InvalidCredentialsError(cause=e) from e

            if "invalid_client" in text or "unauthorized_client" in text:
                logger.error(
                    "keycloak_login_client_misconfigured",
                    extra={"extra": {"kc_error": text[:200]}},
                )
                raise IdentityProviderMisconfiguredError(cause=e) from e

            logger.exception("keycloak_login_auth_error_unexpected")
            raise IdentityProviderUnavailableError(detail=str(e), cause=e) from e

        except KeycloakPostError as e:
            status = get_keycloak_status(e)
            error_text = get_keycloak_error_text(e)

            match status, error_text:
                case (400 | 401), text if "invalid_grant" in text:
                    logger.warning(
                        "keycloak_refresh_token_failed",
                        extra={
                            "extra": {
                                "kc_status": status,
                                "kc_error": text[:200],
                            }
                        },
                    )
                    raise InvalidRefreshTokenError(cause=e) from e
                
                case (400 | 401), text if "invalid_client" in text or "unauthorized_client" in text:
                    logger.warning(
                        "keycloak_refresh_token_failed",
                        extra={
                            "extra": {
                                "kc_status": status,
                                "kc_error": text[:200],
                            }
                        },
                    )
                    raise IdentityProviderMisconfiguredError(cause=e) from e
                
                case (400 | 401), text if "invalid_request" in text:
                    raise BadRequestError(detail=text)

            raise IdentityProviderUnavailableError(
                detail=error_text,
                cause=e
            ) from e

        except Exception as e:
            raise IdentityProviderUnavailableError(cause=e) from e
