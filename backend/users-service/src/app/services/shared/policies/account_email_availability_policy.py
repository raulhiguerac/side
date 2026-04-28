from app.core.exceptions.auth import EmailAlreadyRegisteredError
from app.core.logging.logger import get_logger
from app.core.logging.utils import email_hash
from app.services.auth.ports.unit_of_work import AuthUnitOfWork

logger = get_logger(__name__)

class AccountEmailAvailabilityPolicy:
    def __init__(self, uow: AuthUnitOfWork):
        self.uow = uow

    async def ensure_email_available(self, *, email: str) -> None:
        email_h = email_hash(email)

        existing_account = await self.uow.accounts.get_by_email(email=email)
        if existing_account:
            logger.info(
                "register_email_already_exists",
                extra={"extra": {"email_hash": email_h}},
            )
            raise EmailAlreadyRegisteredError(email=email)
