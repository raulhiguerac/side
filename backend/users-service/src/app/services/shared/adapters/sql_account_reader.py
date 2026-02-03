import uuid
from typing import Optional

from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.services.shared.ports.account_reader import AccountReaderPort

from app.models.account import Account
from app.repositories.account_repository import get_account_by_id, get_account_by_email


class SqlAccountReader(AccountReaderPort):
    """
    Shared DB adapter (read-only).
    - No depende de dominios (auth/user)
    - No lanza errores de dominio
    - Devuelve None si no existe
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    async def get_by_id(self, *, account_id: uuid.UUID) -> Optional[Account]:
        return await run_in_threadpool(
            get_account_by_id,
            self._session,
            account_id,
        )

    async def get_by_email(self, *, email: str) -> Optional[Account]:
        return await run_in_threadpool(
            get_account_by_email,
            self._session,
            email,
        )
