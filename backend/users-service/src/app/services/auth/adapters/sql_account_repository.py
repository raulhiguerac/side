import uuid
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.models.account import Account
from app.services.auth.ports.account_repository import AccountRepository
from app.services.shared.ports.account_reader import AccountReaderPort
from app.core.exceptions.account import AccountNotFoundError 


class SqlAccountRepository(AccountRepository):
    def __init__(self, *, session: Session, reader: AccountReaderPort):
        self._session = session
        self._reader = reader

    async def create_account(self, *, account: Account) -> Account:
        def _create():
            self._session.add(account)
            self._session.flush()
            return account
        return await run_in_threadpool(_create)

    async def get_by_id(self, *, account_id: uuid.UUID) -> Account:
        account = await self._reader.get_by_id(account_id=account_id)
        return account

    async def get_by_email(self, *, email: str) -> Account | None:
        account = await self._reader.get_by_email(email=email)
        return account
