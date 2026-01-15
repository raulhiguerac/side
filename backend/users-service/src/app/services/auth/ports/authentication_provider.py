from typing import Protocol, Dict, Any

from app.schemas.auth import AuthTokens

class AuthenticationProvider(Protocol):
    async def login(self, *, email: str, password: str) -> AuthTokens: ...
    async def refresh_token(self, *, refresh_token: str) -> AuthTokens: ...