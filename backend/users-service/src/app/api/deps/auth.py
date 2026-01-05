import uuid
from typing import Annotated, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.schemas.user import CurrentUserIn

from app.core.exceptions.base import BaseError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def decode_and_verify_jwt(token: str) -> Dict:

    raise NotImplementedError

async def get_current_user_payload(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUserIn:
    try:
        claims = decode_and_verify_jwt(token)
    except Exception as exc:
        raise BaseError(
                message="Invalid token",
                code="INVALID_TOKEN",
                status_code=401,
                cause=exc,
            ) from exc
    
    sub = claims.get("sub")
    if not sub:
        raise BaseError(
                message="Token missing sub claim",
                code="MISSING_SUB_CLAIM",
                status_code=401
            )

    try:
        account_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sub format",
        )

    return account_id