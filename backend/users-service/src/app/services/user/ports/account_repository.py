import uuid
from typing import Protocol

from app.models.account import Account

class AccountRepository(Protocol):
    def get_by_id(self, *, account_id: uuid.UUID) -> Account: ...
    def get_by_email(self, *, email: str) -> Account: ...