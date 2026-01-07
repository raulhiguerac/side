import os
import jwt
from fastapi import Request
from fastapi.concurrency import run_in_threadpool
from jwt import PyJWKClient, PyJWKClientError, PyJWKClientConnectionError

from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    DecodeError,
    InvalidTokenError,
)


from app.core.exceptions.auth import MissingCookieException, InvalidTokenException
from app.core.exceptions.integrations import IdentityProviderUnavailableError

from app.schemas.auth import Principal
from app.core.logging.logger import get_logger

from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)


jwks_url = os.getenv('KC_JWKS_URL')
issuer = os.getenv('KC_ISSUER')
oidc_audience = os.getenv('OIDC_AUDIENCE')

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
        signing_key = await run_in_threadpool(jwks_client.get_signing_key_from_jwt, access_token)
    except PyJWKClientConnectionError as e:
        logger.error(
            "PyJWK connection error",
            extra={"extra": {"detail": str(e)}},
            exc_info=True,
        )
        raise IdentityProviderUnavailableError(detail=str(e),cause=e)
    except PyJWKClientError as e:
        raise InvalidTokenException(cause=e)

    try:
        claims = await run_in_threadpool(
            jwt.decode,
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=oidc_audience,
            issuer=issuer,
        )

    except ExpiredSignatureError as e:
        raise InvalidTokenException(cause=e, detail="Access token expired")
    except (InvalidAudienceError, InvalidIssuerError) as e:
        raise InvalidTokenException(cause=e, detail="Invalid token claims")
    except (InvalidSignatureError, DecodeError) as e:
        raise InvalidTokenException(cause=e, detail="Invalid token signature")
    except InvalidTokenError as e:
        raise InvalidTokenException(cause=e)
    
    sub = claims.get("sub")
    if not sub:
        raise InvalidTokenException(
            detail="Sub is not defined", cause=ValueError("Sub is not defined")
        )

    scope_str = claims.get("scope", "")
    scope = scope_str.split() if scope_str else []

    principal = Principal(
        sub=sub,
        email=claims.get("email"),
        email_verified=claims.get("email_verified") or False,
        scope=scope,
    )

    request.state.principal = principal

    return principal

