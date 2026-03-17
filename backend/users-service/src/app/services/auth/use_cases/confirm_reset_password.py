import uuid

from app.core.exceptions.auth import (
    PasswordsDoNotMatchError,
    TokenInvalidOrExpiredError,
)
from app.services.auth.ports.identity_provider import IdentityProvider
from app.services.auth.ports.unit_of_work import AuthUnitOfWork
from app.services.auth.schemas.passwords import ResetPassword
from app.services.shared.helpers.security import hash_token
from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_keys import reset_password_cache_key

TOKEN_INVALID_OR_EXPIRED_MSG = "Token is invalid or expired"


class ConfirmResetPasswordUseCase:
    """
    Confirms a password reset using a one-time token.

    Flow:
    1) Consume token payload from cache (GETDEL)
    2) Load account
    3) Validate account state (security-friendly)
    4) Validate password confirmation
    5) Reset password via Identity Provider
    """

    def __init__(
        self,
        *,
        idp: IdentityProvider,
        uow: AuthUnitOfWork,
        cache_client: CachePort,
    ) -> None:
        self.idp = idp
        self.uow = uow
        self.cache = cache_client

    async def execute(self, *, token: str, req: ResetPassword) -> None:
        if req.new_password != req.confirm_password:
            raise PasswordsDoNotMatchError()

        payload = await self._consume_token(token=token)
        account_id = self._extract_account_id(payload)

        account = await self.uow.accounts.get_by_id(account_id=account_id)
        if not account:
            raise TokenInvalidOrExpiredError(detail=TOKEN_INVALID_OR_EXPIRED_MSG)

        if not account.is_active:
            return

        await self.idp.reset_password(
            account_id=account_id,
            new_password=req.new_password,
        )

    async def _consume_token(self, *, token: str) -> dict:
        token_hash = hash_token(token)
        cache_key = reset_password_cache_key(token_hash)

        payload = await self.cache.getdel_json(key=cache_key)
        if payload is None:
            raise TokenInvalidOrExpiredError(detail=TOKEN_INVALID_OR_EXPIRED_MSG)

        return payload

    def _extract_account_id(self, payload: dict) -> uuid.UUID:
        account_id = payload.get("account_id")
        if not account_id:
            raise TokenInvalidOrExpiredError(detail=TOKEN_INVALID_OR_EXPIRED_MSG)

        try:
            return uuid.UUID(account_id)
        except ValueError:
            raise TokenInvalidOrExpiredError(detail=TOKEN_INVALID_OR_EXPIRED_MSG)
