from typing import Protocol

from app.services.user.ports.account_repository import AccountRepository
from app.services.user.ports.user_repository import UserRepository


class UserUnitOfWork(Protocol):
    accounts: AccountRepository
    users: UserRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
