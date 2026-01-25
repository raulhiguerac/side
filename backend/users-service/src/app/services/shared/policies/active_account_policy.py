import uuid

from app.core.exceptions.auth import InvalidCredentialsError
from app.core.logging.logger import get_logger
from app.core.logging.utils import email_hash
from app.services.auth.ports.unit_of_work import AuthUnitOfWork

logger = get_logger(__name__)


class AccountActivePolicy:
    def __init__(self, uow: AuthUnitOfWork):
        self.uow = uow

    async def ensure_active_by_email(self, *, email: str) -> None:
        email_h = email_hash(email)

        account = await self.uow.accounts.get_by_email(email=email)
        if not account:
            logger.info("account_not_found_by_email", extra={"extra": {"email_hash": email_h}})
            raise InvalidCredentialsError()

        if not account.is_active:
            logger.info("account_inactive_by_email", extra={"extra": {"email_hash": email_h}})
            raise InvalidCredentialsError()

    async def ensure_active_by_id(self, *, account_id: uuid.UUID) -> None:
        account = await self.uow.accounts.get_by_id(account_id=account_id)
        if not account:
            logger.info("account_not_found_by_id", extra={"extra": {"account_id": str(account_id)}})
            raise InvalidCredentialsError()

        if not account.is_active:
            logger.info("account_inactive_by_id", extra={"extra": {"account_id": str(account_id)}})
            raise InvalidCredentialsError()