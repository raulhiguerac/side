from typing import Protocol

from app.services.user.ports.account_repository import AccountRepository
from app.services.user.ports.onboarding_completion_repository import (
    OnboardingCompletionRepository,
)
from app.services.user.ports.user_repository import UserRepository


class UserUnitOfWork(Protocol):
    accounts: AccountRepository
    users: UserRepository
    onboarding: OnboardingCompletionRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
