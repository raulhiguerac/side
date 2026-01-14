from app.core.logging.logger import get_logger
from app.core.logging.utils import email_hash

from app.core.exceptions.auth import InvalidCredentialsError
from app.schemas.auth import AccountLogin, AuthTokens

from app.services.auth.ports.authentication_provider import AuthenticationProvider
from app.uow.sql_uow import SqlUnitOfWork

logger = get_logger(__name__)


class LoginAccountUseCase:
    def __init__(self, *, uow: SqlUnitOfWork, auth_provider: AuthenticationProvider):
        self.uow = uow
        self.auth_provider = auth_provider

    async def execute(self, req: AccountLogin) -> AuthTokens:
        email_h = email_hash(req.email)

        current_account = self.uow.get_by_email(req.email)
        if not current_account:
            logger.info("login_unknown_email", extra={"extra": {"email_hash": email_h}})
            raise InvalidCredentialsError()

        if not current_account.is_active:
            logger.info("login_blocked_inactive", extra={"extra": {"email_hash": email_h}})
            raise InvalidCredentialsError()

        token = await self.auth_provider.login(email=req.email, password=req.password)

        return token
