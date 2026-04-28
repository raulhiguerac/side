from typing import Literal, NoReturn

from keycloak.exceptions import (
    KeycloakAuthenticationError,
    KeycloakPostError,
)

from app.core.exceptions.auth import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.core.exceptions.identity_provider import (
    IdentityProviderMisconfiguredError,
    IdentityProviderUnavailableError,
)
from app.core.exceptions.validation import BadRequestError
from app.core.logging.logger import get_logger
from app.integrations._utils import (
    get_keycloak_error_text,
    get_keycloak_status,
)

logger = get_logger(__name__)

def translate_keycloak_error(
    *,
    error: Exception,
    operation: Literal["login", "refresh", "revoke"],
) -> NoReturn | None:

    if isinstance(error, KeycloakAuthenticationError):
        text = str(error).lower()

        if "invalid_grant" in text or "invalid user credentials" in text:
            match operation:
                case "login":
                    logger.warning("keycloak_login_invalid_credentials", extra={"extra": {"kc_error": text[:200]}})
                    raise InvalidCredentialsError(cause=error) from error
                case "refresh":
                    logger.warning("keycloak_refresh_token_failed", extra={"extra": {"kc_error": text[:200]}})
                    raise InvalidRefreshTokenError(cause=error) from error
                case "revoke":
                    logger.info("keycloak_revoke_token_already_invalid")
                    return None

        if "invalid_client" in text or "unauthorized_client" in text:
            logger.error("keycloak_client_misconfigured", extra={"extra": {"kc_error": text[:200]}})
            raise IdentityProviderMisconfiguredError(cause=error) from error

        logger.exception("keycloak_auth_error_unexpected")
        raise IdentityProviderUnavailableError(detail=text, cause=error) from error

    if isinstance(error, KeycloakPostError):
        status = get_keycloak_status(error)
        text = (get_keycloak_error_text(error) or "").lower()

        if status in (400, 401) and "invalid_grant" in text:
            match operation:
                case "login":
                    logger.warning("keycloak_login_invalid_credentials", extra={"extra": {"kc_status": status, "kc_error": text[:200]}})
                    raise InvalidCredentialsError(cause=error) from error
                case "refresh":
                    logger.warning("keycloak_refresh_token_failed", extra={"extra": {"kc_status": status, "kc_error": text[:200]}})
                    raise InvalidRefreshTokenError(cause=error) from error
                case "revoke":
                    logger.info("keycloak_revoke_token_already_invalid")
                    return None

        if status in (400, 401) and ("invalid_client" in text or "unauthorized_client" in text):
            logger.error("keycloak_client_misconfigured", extra={"extra": {"kc_status": status, "kc_error": text[:200]}})
            raise IdentityProviderMisconfiguredError(cause=error) from error

        if status in (400, 401) and "invalid_request" in text:
            raise BadRequestError(detail=text, cause=error) from error

        logger.exception("keycloak_post_error_unexpected")
        raise IdentityProviderUnavailableError(detail=text, cause=error) from error

    logger.exception("keycloak_post_error_unexpected", extra={"extra": {"kc_error": str(error).lower()}})
    raise IdentityProviderUnavailableError(cause=error) from error
