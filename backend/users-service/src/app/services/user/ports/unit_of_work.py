from typing import Protocol

from app.services.user.ports.account_repository import AccountRepository
from app.services.user.ports.user_repository import UserRepository


class UserUnitOfWork(Protocol):
    accounts: AccountRepository
    users: UserRepository

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
