# from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.shared.helpers.security import hash_token

from app.core.exceptions.auth import TokenInvalidOrExpiredError
from app.models.account import AccountActionActor
from app.services.user.helpers.cache_keys import reactivation_cache_key
from app.services.shared.ports.cache import CachePort
from app.services.user.ports.unit_of_work import UserUnitOfWork


TOKEN_INVALID_OR_EXPIRED_MSG = "Token is invalid or expired"


class ConfirmReactivationUseCase:
    """
    Confirms an account reactivation using a one-time token.

    Flow:
    1) Consume token payload from cache (GETDEL)
    2) Load account
    3) If already active -> no-op (idempotent)
    4) Reactivate + commit
    """

    def __init__(self, *, uow: UserUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache = cache_client

    async def execute(self, *, token: str) -> None:
        payload = await self._consume_token(token=token)
        account_id = self._extract_account_id(payload)

        account = await self.uow.accounts.get_by_id(account_id=account_id)
        if not account:
            raise TokenInvalidOrExpiredError(detail=TOKEN_INVALID_OR_EXPIRED_MSG)

        if account.is_active:
            return

        self._reactivate(account)

        try:
            await self.uow.commit()
        except Exception:
            await self.uow.rollback()
            raise

    async def _consume_token(self, *, token: str) -> dict | list:
        token_hash = hash_token(token)
        cache_key = reactivation_cache_key(token_hash)
        payload = await self.cache.getdel_json(key=cache_key)

        if payload is None:
            raise TokenInvalidOrExpiredError(detail=TOKEN_INVALID_OR_EXPIRED_MSG)

        return payload

    def _extract_account_id(self, payload: dict | list) -> Any:
        if not isinstance(payload, dict):
            raise TokenInvalidOrExpiredError(detail=TOKEN_INVALID_OR_EXPIRED_MSG)

        account_id = payload.get("account_id")
        if not account_id:
            raise TokenInvalidOrExpiredError(detail=TOKEN_INVALID_OR_EXPIRED_MSG)

        return account_id

    def _reactivate(self, account: Any) -> None:
        account.is_active = True
        account.deactivated_at = None
        account.deactivated_by = None
        account.deactivation_reason = None
        account.reactivated_at = datetime.utcnow()
        account.reactivated_by = AccountActionActor.user
