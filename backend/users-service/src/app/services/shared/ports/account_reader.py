import uuid
from typing import Protocol

from app.models.account import Account


class AccountReaderPort(Protocol):
    async def get_by_id(self, *, account_id: uuid.UUID) -> Account | None: ...
    async def get_by_email(self, *, email: str) -> Account | None: ...
    async def get_accounts_bulk(
        self, *, account_ids: list[uuid.UUID]
    ) -> list[tuple[uuid.UUID, str]]: ...
