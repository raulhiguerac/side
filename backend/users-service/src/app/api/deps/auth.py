import os
import uuid
from functools import partial

import jwt
from fastapi import Request
from fastapi.concurrency import run_in_threadpool
from jwt import PyJWKClient, PyJWKClientConnectionError, PyJWKClientError
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    InvalidTokenError,
)

from app.core.exceptions.auth import InvalidTokenException, MissingCookieException
from app.core.exceptions.identity_provider import IdentityProviderUnavailableError
from app.core.logging.logger import get_logger
from app.schemas.common import Principal
from app.services.auth.schemas.tokens import RefreshToken

logger = get_logger(__name__)

jwks_url = os.getenv("KC_JWKS_URL")
issuer = os.getenv("KC_ISSUER")
oidc_audience = os.getenv("OIDC_AUDIENCE")

if not jwks_url:
    raise RuntimeError("JWKS URL is not set")
if not issuer:
    raise RuntimeError("ISSUER is not set")
if not oidc_audience:
    raise RuntimeError("OIDC_AUDIENCE is not set")

jwks_client = PyJWKClient(jwks_url)


async def get_current_principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if principal is not None:
        return principal

    access_token = request.cookies.get("access_token")
    if not access_token:
        raise MissingCookieException(cause=ValueError("Access token is not set"))

    try:
        signing_key = await run_in_threadpool(
            jwks_client.get_signing_key_from_jwt, access_token
        )
    except PyJWKClientConnectionError as e:
        logger.error(
            "jwks_connection_error",
            extra={"extra": {"detail": str(e)}},
            exc_info=True,
        )
        raise IdentityProviderUnavailableError(detail=str(e), cause=e)
    except PyJWKClientError as e:
        raise InvalidTokenException(cause=e)

    try:
        claims = await run_in_threadpool(
            partial(
                jwt.decode,
                access_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=oidc_audience,
                issuer=issuer,
            )
        )
    except ExpiredSignatureError as e:
        raise InvalidTokenException(cause=e, detail="Access token expired")
    except (InvalidAudienceError, InvalidIssuerError) as e:
        raise InvalidTokenException(cause=e, detail="Invalid token claims")
    except (InvalidSignatureError, DecodeError) as e:
        raise InvalidTokenException(cause=e, detail="Invalid token signature")
    except InvalidTokenError as e:
        raise InvalidTokenException(cause=e)

    sub_raw = claims.get("sub")
    if not sub_raw:
        raise InvalidTokenException(
            detail="Sub is not defined", cause=ValueError("Sub is not defined")
        )

    try:
        sub = uuid.UUID(str(sub_raw))
    except (ValueError, TypeError) as e:
        raise InvalidTokenException(detail="Invalid subject (sub) claim", cause=e)

    scope_str = claims.get("scope", "") or ""
    scope = scope_str.split() if isinstance(scope_str, str) and scope_str else []

    principal = Principal(
        sub=sub,
        email=claims.get("email"),
        email_verified=bool(claims.get("email_verified", False)),
        scope=scope,
    )

    request.state.principal = principal
    return principal


async def get_refresh_token_from_cookie(request: Request) -> RefreshToken:
    token = request.cookies.get("refresh_token")
    if not token:
        raise MissingCookieException(cause=ValueError("Missing refresh token cookie"))
    return RefreshToken(refresh_token=token)


async def get_refresh_token_from_cookie_optional(request: Request) -> RefreshToken | None:
    token = request.cookies.get("refresh_token")
    if not token:
        return None
    return RefreshToken(refresh_token=token)