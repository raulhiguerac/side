from typing import Protocol

from app.services.auth.ports.account_repository import AccountRepository
from app.services.auth.ports.profile_repository import ProfileWriter
from app.services.auth.ports.compensation_task import CompensationTaskRepository


class AuthUnitOfWork(Protocol):
    accounts: AccountRepository
    profiles: ProfileWriter
    compensation_tasks: CompensationTaskRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
