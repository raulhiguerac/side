from app.core.logging.logger import get_logger
from app.core.logging.utils import email_hash

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.auth import InvalidCredentialsError
from app.schemas.auth import AccountLogin, AuthTokens

from app.services.auth.ports.authentication_provider import AuthenticationProvider
from app.services.shared.policies.active_account_policy import AccountActivePolicy

logger = get_logger(__name__)


class AuthenticateAccountUseCase:
    def __init__(self, *, auth_provider: AuthenticationProvider, account_guard: AccountActivePolicy):
        self.account_guard = account_guard
        self.auth_provider = auth_provider

    async def login(self, *, req: AccountLogin) -> AuthTokens:
        await self.account_guard.ensure_active_by_email(email = req.email)
        return await self.auth_provider.login(email=req.email, password=req.password)

    async def refresh_token(self, *, refresh_token: str) -> AuthTokens:
        return await self.auth_provider.refresh_token(refresh_token=refresh_token)
