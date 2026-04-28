import uuid
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.core.exceptions.base import BaseError
from app.core.logging.logger import get_logger
from app.core.logging.utils import email_hash

from app.models.account import Account, OnboardingStep
from app.models.kc_tasks import KcTaskType

from app.services.auth.schemas.registration import RegisterRequest

from app.services.auth.schemas.compensation import CreateKcCompensationTask

from app.services.shared.db.db_error_translator import DbErrorTranslator
from app.services.auth.helpers.profile_factory import ProfileFactory
from app.services.auth.ports.identity_provider import IdentityProvider

from app.services.shared.policies.account_email_availability_policy import (
    AccountEmailAvailabilityPolicy,
)
from app.services.auth.ports.unit_of_work import AuthUnitOfWork

logger = get_logger(__name__)


class RegisterAccountUseCase:
    def __init__(
        self,
        *,
        uow: AuthUnitOfWork,
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

    async def _enqueue_delete_kc_user_task(
        self,
        *,
        kc_user_id: Optional[uuid.UUID],
        email: str,
        error: Exception,
    ) -> None:
        if not kc_user_id:
            return

        await self.uow.compensation_tasks.add(
            cmd=CreateKcCompensationTask(
                kc_user_id=kc_user_id,
                email=email,
                task_type=KcTaskType.delete_kc_user,
                last_error=f"{type(error).__name__}: {str(error)[:500]}",
                attempts=0
            )
        )

    async def register(self, *, req: RegisterRequest) -> Account:
        email_h = email_hash(req.email)
        logger.info(
            "register_email_check_started",
            extra={"extra": {"email_hash": email_h}},
        )

        await self.email_policy.ensure_email_available(email=req.email)

        logger.info(
            "register_email_check_ok",
            extra={"extra": {"email_hash": email_h}},
        )

        kc_user_id: Optional[uuid.UUID] = None

        try:
            kc_user_id = await self.idp.create_account(email=req.email, password=req.password)

            account = Account(
                account_id=kc_user_id,
                email=req.email,
                account_type=req.account_type,
                onboarding_step=OnboardingStep.intent,
            )
            await self.uow.accounts.create_account(account=account)

            profile = self.profile_factory.from_register(req=req, account_id=kc_user_id)
            await self.uow.profiles.create_profile(profile=profile)

            await self.uow.commit()

            logger.info(
                "register_ok",
                extra={"extra": {"email_hash": email_h, "kc_user_id": str(kc_user_id)}},
            )
            return account

        except IntegrityError as e:
            await self.uow.rollback()
            try:
                await self.idp.delete_account(kc_user_id)
            except Exception as delete_err:
                await self._enqueue_delete_kc_user_task(
                    kc_user_id=kc_user_id,
                    email=req.email,
                    error=delete_err,
                )
            raise self.db_errors.translate_integrity_error(
                e, email=req.email, kc_user_id=kc_user_id
            ) from e

        except BaseError as e:
            await self.uow.rollback()
            await self._enqueue_delete_kc_user_task(
                kc_user_id=kc_user_id,
                email=req.email,
                error=e,
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

            await self.uow.rollback()
            await self._enqueue_delete_kc_user_task(
                kc_user_id=kc_user_id,
                email=req.email,
                error=e,
            )

            raise BaseError(
                message="An error occurred while registering the account",
                code="REGISTER_FAILED",
                context={
                    "email_hash": email_h,
                    "kc_user_id": str(kc_user_id) if kc_user_id else None,
                    "error_type": type(e).__name__,
                },
                cause=e,
            ) from e
