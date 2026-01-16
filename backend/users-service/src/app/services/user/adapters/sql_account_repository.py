import uuid
from typing import Optional
from sqlmodel import Session

from app.models.account import Account
from app.repositories.account_repository import (
    get_account_by_id,
)

from app.services.user.ports.account_repository import AccountRepository


class SqlAccountRepository(AccountRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, *, account_id: uuid.UUID) -> Optional[Account]:
        return get_account_by_id(self._session, account_id)