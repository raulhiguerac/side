from fastapi import Response
from app.schemas.auth import AuthTokens


def set_auth_cookies(
    *,
    response: Response,
    tokens: AuthTokens,
    secure: bool = False,
    samesite: str = "lax",
) -> None:
    """
    Setea cookies de autenticación (access + refresh).
    """
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
        max_age=tokens.expires_in,
    )

    if tokens.refresh_token and tokens.refresh_expires_in:
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=secure,
            samesite=samesite,
            path="/",
            max_age=tokens.refresh_expires_in,
        )

def delete_auth_cookies(
    *,
    response: Response,
) -> None:
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
