from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.services.auth.ports.unit_of_work import AuthUnitOfWork
from app.services.auth.ports.compensation_task import (
    CompensationTaskRepository,
)
from app.services.auth.ports.profile_registration_writer import (
    ProfileWriter,
)
from app.services.auth.ports.email_recipient_reader import (
    EmailRecipientReaderPort,
)

from app.services.shared.ports.account_reader import AccountReaderPort

from app.services.shared.adapters.sql_account_reader import (
    SqlAccountReader,
)
from app.services.auth.adapters.sql_account_repository import (
    SqlAccountRepository,
)
from app.services.auth.adapters.sql_profile_registration_writer import (
    SqlProfileRepository,
)
from app.services.auth.adapters.sql_email_recipient_reader import (
    SqlEmailRecipientReader,
)
from app.services.auth.adapters.sql_compensation_task import (
    SqlCompensationTaskRepository,
)


class SqlAuthUnitOfWork(AuthUnitOfWork):
    def __init__(self, *, session: Session) -> None:
        self._session = session

        account_reader: AccountReaderPort = SqlAccountReader(
            session=session
        )

        self.accounts = SqlAccountRepository(
            session=session,
            reader=account_reader,
        )

        self.profiles: ProfileWriter = SqlProfileRepository(
            session=session
        )

        self.email_recipients: EmailRecipientReaderPort = (
            SqlEmailRecipientReader(session=session)
        )

        self.compensation_tasks: CompensationTaskRepository = (
            SqlCompensationTaskRepository(session=session)
        )

    async def commit(self) -> None:
        await run_in_threadpool(self._session.commit)

    async def rollback(self) -> None:
        await run_in_threadpool(self._session.rollback)
