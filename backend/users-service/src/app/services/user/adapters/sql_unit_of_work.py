from sqlmodel import Session

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

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
