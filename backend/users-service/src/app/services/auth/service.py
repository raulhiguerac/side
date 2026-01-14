import uuid
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.core.logging.utils import email_hash

from app.models.account import Account

from app.schemas.auth import AccountLogin, AuthTokens, RegisterRequest

from app.services.auth.ports.identity_provider import IdentityProvider
from app.services.auth.ports.authentication_provider import AuthenticationProvider


from app.core.exceptions.auth import InvalidCredentialsError


from sqlmodel import Session
from app.uow.sql_uow import SqlUnitOfWork
from app.services.auth.use_cases.register_account import RegisterAccountUseCase
from app.services.auth.use_cases.login_account import LoginAccountUseCase
from app.services.auth.helpers.profile_factory import ProfileFactory
from app.services.auth.helpers.db_error_translator import DbErrorTranslator
from app.services.auth.helpers.compensation import try_delete_idp_user_or_enqueue

from app.core.logging.logger import get_logger
logger = get_logger(__name__)

async def create_account_service(
        *,
        session: Session,
        idp: IdentityProvider,
        req: RegisterRequest,
    ) -> Account:
    uow = SqlUnitOfWork(session)

    uc = RegisterAccountUseCase(
        uow=uow,
        idp=idp,
        profile_factory=ProfileFactory(),
        db_errors=DbErrorTranslator(),
    )

    return await uc.execute(req)

async def create_access_token_service(
        *,
        session: Session,
        auth_provider: AuthenticationProvider,
        req: AccountLogin
    ) -> AuthTokens:
    uow = SqlUnitOfWork(session)

    uc = LoginAccountUseCase(
        uow=uow,
        auth_provider=auth_provider,
    )

    return await uc.execute(req)
