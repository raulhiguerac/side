import uuid
from typing import Protocol

from app.models.account import Account
from app.services.user.schemas.current import UserInterestsResponse


class AccountRepository(Protocol):
    async def get_by_id(self, *, account_id: uuid.UUID) -> Account: ...
    async def get_by_email(self, *, email: str) -> Account: ...
    async def get_interests(self, *, account_id: uuid.UUID) -> UserInterestsResponse: ...