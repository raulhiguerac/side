import uuid
from typing import Optional

from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session, col, select

from app.models.account import Account
from app.models.interests import (
    UserInterest,
    UserNeighborhoodInterest,
    UserPropertyTypeInterest,
)
from app.repositories.account_repository import get_account_by_email, get_account_by_id
from app.services.shared.ports.account_reader import AccountReaderPort


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

    async def get_interests_by_account(self, *, account_id: uuid.UUID) -> dict:
        def _query():
            localities = self._session.exec(
                select(UserInterest)
                .where(UserInterest.account_id == account_id)
                .where(UserInterest.is_active == True)  # noqa: E712
            ).all()

            if not localities:
                return {"localities": [], "neighborhoods": [], "properties": []}

            interest_ids = [loc.id for loc in localities]

            neighborhoods = self._session.exec(
                select(UserNeighborhoodInterest)
                .where(col(UserNeighborhoodInterest.user_interest_id).in_(interest_ids))
                .order_by(UserNeighborhoodInterest.interest_rank)
            ).all()

            properties = self._session.exec(
                select(UserPropertyTypeInterest)
                .where(col(UserPropertyTypeInterest.user_interest_id).in_(interest_ids))
            ).all()

            return {"localities": localities, "neighborhoods": neighborhoods, "properties": properties}

        return await run_in_threadpool(_query)
