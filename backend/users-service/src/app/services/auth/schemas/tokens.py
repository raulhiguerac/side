from typing import Optional

from app.schemas.base import StrictBase


class AuthTokens(StrictBase):
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    refresh_expires_in: Optional[int] = None
    token_type: str = "Bearer"

class RefreshToken(StrictBase):
    refresh_token: str