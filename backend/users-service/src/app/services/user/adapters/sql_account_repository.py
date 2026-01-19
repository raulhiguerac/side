import uuid

from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.core.exceptions.user import AccountNotFoundError
from app.models.account import Account
from app.repositories.account_repository import get_account_by_id
from app.services.user.ports.account_repository import AccountRepository


class SqlAccountRepository(AccountRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_by_id(self, *, account_id: uuid.UUID) -> Account:
        account = await run_in_threadpool(
            get_account_by_id,
            self._session,
            account_id,
        )

        if account is None:
            raise AccountNotFoundError(account_id=account_id)

        return account
