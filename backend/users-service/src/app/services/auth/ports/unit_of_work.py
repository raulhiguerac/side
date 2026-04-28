from typing import Protocol

from app.services.auth.ports.account_repository import AccountRepository
from app.services.auth.ports.compensation_task import CompensationTaskRepository
from app.services.auth.ports.email_recipient_reader import EmailRecipientReaderPort
from app.services.auth.ports.profile_registration_writer import ProfileWriter


class AuthUnitOfWork(Protocol):
    accounts: AccountRepository
    profiles: ProfileWriter
    email_recipients: EmailRecipientReaderPort
    compensation_tasks: CompensationTaskRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
