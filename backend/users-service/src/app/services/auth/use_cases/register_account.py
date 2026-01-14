import uuid

from sqlalchemy.exc import IntegrityError

from app.schemas.auth import RegisterRequest

from app.models.account import Account

from app.uow.sql_uow import SqlUnitOfWork
from app.services.auth.ports.identity_provider import IdentityProvider

from app.services.auth.helpers.profile_factory import ProfileFactory
from app.services.auth.helpers.db_error_translator import DbErrorTranslator
from app.services.auth.helpers.compensation import try_delete_idp_user_or_enqueue

from app.core.logging.utils import email_hash
from app.core.exceptions.base import BaseError
from app.core.exceptions.auth import EmailAlreadyRegisteredError

from app.core.logging.logger import get_logger

logger = get_logger(__name__)

class RegisterAccountUseCase:
    def __init__(
        self,
        *,
        uow: SqlUnitOfWork,
        idp: IdentityProvider,
        profile_factory: ProfileFactory,
        db_errors: DbErrorTranslator,
    ):
        self.uow = uow
        self.idp = idp
        self.profile_factory = profile_factory
        self.db_errors = db_errors

    async def execute(self, req: RegisterRequest) -> Account:
        logger.info("db_email_check_started", extra={"extra": {"email_hash": email_hash(req.email)}})

        if self.uow.get_by_email(req.email):
            logger.info("db_email_check_result", extra={"extra": {"found": True}})
            raise EmailAlreadyRegisteredError(email=req.email)

        logger.info("db_email_check_result", extra={"extra": {"found": False}})

        kc_user_id: uuid.UUID | None = None

        try:
            kc_user_id = await self.idp.create_account(email=req.email, password=req.password)

            account = Account(
                account_id=kc_user_id,
                email=req.email,
                account_type=req.account_type,
                onboarding_step=1,
            )
            self.uow.add_account(account)

            profile = self.profile_factory.from_register(req=req, account_id=kc_user_id)
            self.uow.add_profile(profile)

            self.uow.commit()

            logger.info("account_register_ok", extra={"extra": {"kc_user_id": str(kc_user_id)}})
            return account

        except IntegrityError as e:
            self.uow.safe_rollback(kc_user_id = kc_user_id)

            await try_delete_idp_user_or_enqueue(
                session=self.uow.session,
                idp=self.idp,
                kc_user_id=kc_user_id,
                email=req.email,
                reason=e,
            )

            raise self.db_errors.translate_integrity_error(e, email=req.email, kc_user_id=kc_user_id) from e

        except BaseError:
            self.uow.safe_rollback(kc_user_id = kc_user_id)
            await try_delete_idp_user_or_enqueue(
                session=self.uow.session,
                idp=self.idp,
                kc_user_id=kc_user_id,
                email=req.email,
                reason=None,
            )
            raise

        except Exception as e:
            logger.exception("user_register_failed", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})
            self.uow.safe_rollback(kc_user_id = kc_user_id)

            await try_delete_idp_user_or_enqueue(
                kc_user_id=kc_user_id,
                email=req.email,
                reason=e,
            )

            raise BaseError(
                message="An error occurred while saving the user profile",
                code="DATABASE_ERROR",
                status_code=500,
                context={
                    "email_hash": email_hash(req.email),
                    "kc_user_id": str(kc_user_id) if kc_user_id else None,
                    "db_error_type": type(e).__name__,
                },
                cause=e,
            ) from e
