import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.core.exceptions.base import BaseError
from app.core.logging.logger import get_logger
from app.core.logging.utils import email_hash

from app.models.account import Account
from app.schemas.auth import RegisterRequest

from app.services.auth.helpers.compensation import try_delete_idp_user_or_enqueue
from app.services.auth.helpers.db_error_translator import DbErrorTranslator
from app.services.auth.helpers.profile_factory import ProfileFactory
from app.services.auth.ports.identity_provider import IdentityProvider

from app.services.shared.policies.account_email_availability_policy import (
    AccountEmailAvailabilityPolicy,
)
from app.uow.sql_uow import SqlUnitOfWork

logger = get_logger(__name__)


class RegisterAccountUseCase:
    def __init__(
        self,
        *,
        uow: SqlUnitOfWork,
        idp: IdentityProvider,
        email_policy: AccountEmailAvailabilityPolicy,
        profile_factory: ProfileFactory,
        db_errors: DbErrorTranslator,
    ):
        self.uow = uow
        self.idp = idp
        self.email_policy = email_policy
        self.profile_factory = profile_factory
        self.db_errors = db_errors

    async def register(self, *, req: RegisterRequest) -> Account:
        email_h = email_hash(req.email)
        logger.info("register_email_check_started", extra={"extra": {"email_hash": email_h}})

        await self.email_policy.ensure_email_available(email=req.email)

        logger.info("register_email_check_ok", extra={"extra": {"email_hash": email_h}})

        kc_user_id: Optional[uuid.UUID] = None

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

            logger.info(
                "register_ok",
                extra={"extra": {"email_hash": email_h, "kc_user_id": str(kc_user_id)}},
            )
            return account

        except IntegrityError as e:
            self.uow.safe_rollback(kc_user_id=kc_user_id)

            await try_delete_idp_user_or_enqueue(
                session=self.uow.session,
                idp=self.idp,
                kc_user_id=kc_user_id,
                email=req.email,
                reason=e,
            )

            raise self.db_errors.translate_integrity_error(
                e, email=req.email, kc_user_id=kc_user_id
            ) from e

        except BaseError as e:
            self.uow.safe_rollback(kc_user_id=kc_user_id)

            await try_delete_idp_user_or_enqueue(
                session=self.uow.session,
                idp=self.idp,
                kc_user_id=kc_user_id,
                email=req.email,
                reason=e,
            )
            raise

        except Exception as e:
            logger.exception(
                "register_failed",
                extra={
                    "extra": {
                        "email_hash": email_h,
                        "kc_user_id": str(kc_user_id) if kc_user_id else None,
                        "error_type": type(e).__name__,
                    }
                },
            )

            self.uow.safe_rollback(kc_user_id=kc_user_id)

            await try_delete_idp_user_or_enqueue(
                session=self.uow.session,
                idp=self.idp,
                kc_user_id=kc_user_id,
                email=req.email,
                reason=e,
            )

            raise BaseError(
                message="An error occurred while saving the user profile",
                code="DATABASE_ERROR",
                status_code=500,
                context={
                    "email_hash": email_h,
                    "kc_user_id": str(kc_user_id) if kc_user_id else None,
                    "db_error_type": type(e).__name__,
                },
                cause=e,
            ) from e