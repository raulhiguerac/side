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

from app.core.config.settings import settings
from app.core.exceptions.auth import UnauthorizedError
from app.schemas.principal import Principal

_jwks_client = PyJWKClient(settings.KC_JWKS_URL)


async def get_current_principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if principal is not None:
        return principal

    token = request.cookies.get("access_token")
    if not token:
        raise UnauthorizedError(detail="Missing access_token cookie")

    try:
        signing_key = await run_in_threadpool(
            _jwks_client.get_signing_key_from_jwt, token
        )
    except PyJWKClientConnectionError as exc:
        raise UnauthorizedError(detail="Could not reach JWKS endpoint", cause=exc)
    except PyJWKClientError as exc:
        raise UnauthorizedError(cause=exc)

    try:
        claims = await run_in_threadpool(
            partial(
                jwt.decode,
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.OIDC_AUDIENCE,
                issuer=settings.KC_ISSUER,
            )
        )
    except ExpiredSignatureError as exc:
        raise UnauthorizedError(detail="Token expired", cause=exc)
    except (InvalidAudienceError, InvalidIssuerError) as exc:
        raise UnauthorizedError(detail="Invalid token claims", cause=exc)
    except (InvalidSignatureError, DecodeError) as exc:
        raise UnauthorizedError(detail="Invalid token signature", cause=exc)
    except InvalidTokenError as exc:
        raise UnauthorizedError(cause=exc)

    sub_raw = claims.get("sub")
    if not sub_raw:
        raise UnauthorizedError(detail="Missing sub claim")

    try:
        sub = uuid.UUID(str(sub_raw))
    except (ValueError, TypeError) as exc:
        raise UnauthorizedError(detail="Invalid sub claim", cause=exc)

    roles: list[str] = claims.get("realm_access", {}).get("roles", [])

    principal = Principal(
        sub=sub,
        email=claims.get("email"),
        email_verified=bool(claims.get("email_verified", False)),
        roles=roles,
    )
    request.state.principal = principal
    return principal
