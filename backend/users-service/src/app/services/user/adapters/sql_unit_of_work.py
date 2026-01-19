from sqlmodel import Session
from fastapi.concurrency import run_in_threadpool

from app.services.user.adapters.sql_account_repository import (
    SqlAccountRepository,
)
from app.services.user.adapters.sql_user_repository import (
    SqlUserRepository
)
from app.services.user.ports.unit_of_work import UserUnitOfWork


class SqlUserUnitOfWork(UserUnitOfWork):
    def __init__(self, session: Session) -> None:
        self._session = session
        self.accounts = SqlAccountRepository(session)
        self.users = SqlUserRepository(session)

    async def commit(self) -> None:
        await run_in_threadpool(self._session.commit)

    async def rollback(self) -> None:
        await run_in_threadpool(self._session.rollback)
