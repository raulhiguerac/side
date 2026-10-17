
from app.schemas.base import StrictBase


class AuthTokens(StrictBase):
    access_token: str
    expires_in: int
    refresh_token: str | None = None
    refresh_expires_in: int | None = None
    token_type: str = "Bearer"

class RefreshToken(StrictBase):
    refresh_token: str