import uuid
from typing import Optional

from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session, select

from app.models.account import (
    AccountType,
    UserProfile,
    CompanyProfile,
)
from app.services.auth.ports.email_recipient_reader import (
    EmailRecipientReaderPort,
)


class SqlEmailRecipientReader(EmailRecipientReaderPort):
    def __init__(self, *, session: Session) -> None:
        self._session = session

    async def get_display_name_by_account_id(
        self,
        *,
        account_id: uuid.UUID,
        account_type: AccountType,
    ) -> Optional[str]:
        if account_type == AccountType.person:
            return await self._get_person_name(account_id)

        if account_type == AccountType.organization:
            return await self._get_organization_name(account_id)

        return None

    async def _get_person_name(self, account_id: uuid.UUID) -> Optional[str]:
        def query() -> Optional[str]:
            stmt = (
                select(UserProfile.first_name)
                .where(UserProfile.account_id == account_id)
            )
            return self._session.exec(stmt).first()

        return await run_in_threadpool(query)

    async def _get_organization_name(self, account_id: uuid.UUID) -> Optional[str]:
        def query() -> Optional[str]:
            stmt = (
                select(CompanyProfile.display_name)
                .where(CompanyProfile.account_id == account_id)
            )
            return self._session.exec(stmt).first()

        return await run_in_threadpool(query)