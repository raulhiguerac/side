import uuid
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from typing import TypeVar

from sqlalchemy.exc import IntegrityError

from app.core.logging.utils import email_hash

from app.models.user import(
    Accounts,
    UserProfile,
    CompanyProfile,
    KcCompensationTask,
    KcTaskType,
    KcTaskStatus
)
from app.schemas.user import UserGeneric, CompanyGeneric
from app.repositories.user import (
    create_user_repo, 
    create_user_profile,
    get_user_by_email
)

from app.integrations.keycloak_client import KeycloakIntegration

from app.core.exceptions.base import BaseError
from app.core.exceptions.user import EmailAlreadyRegisteredError
from app.core.exceptions.integrations import KeycloakDeleteAccountError

from app.core.logging.logger import get_logger
logger = get_logger(__name__)

TAccount = TypeVar("TAccount", UserGeneric, CompanyGeneric)

async def create_account_keycloak(keycloak:KeycloakIntegration, account: TAccount) -> uuid.UUID:

    logger.info("kc_user_create_started", extra={"extra": {"email_hash": email_hash(account.email)}})

    keycloak_uuid = await run_in_threadpool(
        keycloak.create_account_record,
        account.email
    )

    try:
        await run_in_threadpool(
            keycloak.set_password,
            keycloak_uuid,
            account.password,
        )
        logger.info("kc_user_create_succeeded", extra={"extra": {"kc_user_id": str(keycloak_uuid)}})
        return keycloak_uuid

    except Exception as set_pwd_exc:
        logger.warning("kc_user_set_password_failed", extra={"extra": {"kc_user_id": str(keycloak_uuid)}}, exc_info=True)
        try:
            await run_in_threadpool(keycloak.delete_account, keycloak_uuid)
            logger.info("kc_user_delete_succeeded", extra={"extra": {"kc_user_id": str(keycloak_uuid)}})

        except KeycloakDeleteAccountError as delete_exc:
            logger.error(
                "kc_user_delete_account_failed",
                extra={"extra": {"kc_user_id": str(keycloak_uuid)}},
                exc_info=True,
            )
            raise delete_exc from set_pwd_exc
        
        except Exception as delete_exc:
            logger.error(
                "kc_user_delete_account_failed",
                extra={"extra": {"kc_user_id": str(keycloak_uuid)}},
                exc_info=True,
            )
            raise KeycloakDeleteAccountError(
                detail=str(delete_exc),
                user_id=str(keycloak_uuid),
                cause=delete_exc
            ) from set_pwd_exc

        raise

def _persist_compensation_task_safe(session: Session, task: KcCompensationTask, *, log_extra: dict) -> None:
    """
    Persiste una task de compensación con commit seguro (y rollback si el commit falla).
    """
    try:
        session.add(task)
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("kc_compensation_task_persist_failed", extra={"extra": log_extra})

async def create_account_service(session: Session, account: TAccount) -> Accounts:

    existing_account = get_user_by_email(session, account.email)
    if existing_account:
        raise EmailAlreadyRegisteredError(email=account.email)

    keycloak = KeycloakIntegration()

    kc_user_id: uuid.UUID | None = None

    try:

        kc_user_id = await create_account_keycloak(keycloak, account)

        user_data = account.model_dump(exclude={"password"})
        new_user = Accounts(
            account_id=kc_user_id,
            email=user_data["email"],
            account_type=user_data["account_type"],
            onboarding_step=1
        )
        create_user_repo(session, new_user)

        if isinstance(account,UserGeneric):
            user_profile = UserProfile(
                account_id=kc_user_id,
                first_name=account.first_name,
                last_name=account.last_name,
                phone=account.phone,
                intent=getattr(account, "intent", None),
                photo_url=getattr(account, "photo_url", None),
                description=getattr(account, "description", None),
                profile_score=10,
            )
            create_user_profile(session, user_profile)

        elif isinstance(account,CompanyGeneric):
            company_profile = CompanyProfile(
                account_id=kc_user_id,
                display_name=account.display_name,
                phone=account.phone,
                intent=getattr(account, "intent", None),
                photo_url=getattr(account, "photo_url", None),
                description=getattr(account, "description", None),
                profile_score=10
            )
            create_user_profile(session, company_profile)

        session.commit()
        
        logger.info("user_register_ok", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})
        return new_user
    
    except KeycloakDeleteAccountError as kc_del_exc:
        # ✅ Caso: set_password falló y delete “en caliente” también falló.
        # El usuario quedó vivo en Keycloak -> agendar compensación.
        try:
            session.rollback()
        except Exception:
            logger.exception("db_rollback_failed", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})

        # user_id viene en el error, úsalo como fuente de verdad
        # (si tu BaseError guarda context distinto, ajusta esta extracción)
        leaked_kc_user_id = None
        try:
            leaked_kc_user_id = uuid.UUID(kc_del_exc.context.get("user_id"))  # type: ignore[attr-defined]
        except Exception:
            # fallback: si no hay context, usa kc_user_id si existe
            leaked_kc_user_id = kc_user_id

        if leaked_kc_user_id:
            task = KcCompensationTask(
                kc_user_id=leaked_kc_user_id,
                email=account.email,
                task_type=KcTaskType.delete_kc_user,
                status=KcTaskStatus.pending,
                last_error=str(kc_del_exc),
                attempts=0,
            )
            _persist_compensation_task_safe(
                session,
                task,
                log_extra={"kc_user_id": str(leaked_kc_user_id), "email_hash": email_hash(account.email)},
            )

        raise

    except IntegrityError as db_exc:
        try:
            session.rollback()
        except Exception:
            logger.exception("db_rollback_failed", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})

        # Si alcanzamos a crear KC en este request, compensamos borrándolo
        if kc_user_id:
            try:
                await run_in_threadpool(keycloak.delete_account, kc_user_id)
                logger.info("kc_user_delete_succeeded", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})
            except Exception as kc_exc:
                logger.error(
                    "kc_user_delete_failed",
                    extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}},
                    exc_info=True,
                )
                task = KcCompensationTask(
                    kc_user_id=kc_user_id,
                    email=account.email,
                    task_type=KcTaskType.delete_kc_user,
                    status=KcTaskStatus.pending,
                    last_error=f"{type(kc_exc).__name__}: {str(kc_exc)[:500]}",
                    attempts=0,
                )
                _persist_compensation_task_safe(
                    session,
                    task,
                    log_extra={"kc_user_id": str(kc_user_id) if kc_user_id else None, "email_hash": email_hash(account.email)},
                )

        # Finalmente, responde conflicto
        raise EmailAlreadyRegisteredError(email=account.email) from db_exc

    except Exception as db_exc:
        logger.exception(
            "user_register_db_failed",
            extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None, "err_type": type(db_exc).__name__}},
        )

        try:
            session.rollback()
        except Exception:
            logger.exception("db_rollback_failed", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})

        if kc_user_id:
            try:
                await run_in_threadpool(keycloak.delete_account, kc_user_id)
                logger.info("kc_user_delete_succeeded", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})
            except Exception as kc_exc:
                logger.error(
                    "kc_user_delete_failed",
                    extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}},
                    exc_info=True,
                )
                task = KcCompensationTask(
                    kc_user_id=kc_user_id,
                    email=account.email,
                    task_type=KcTaskType.delete_kc_user,
                    status=KcTaskStatus.pending,
                    last_error=f"{type(kc_exc).__name__}: {str(kc_exc)[:500]}",
                    attempts=0,
                )
                _persist_compensation_task_safe(
                    session,
                    task,
                    log_extra={"kc_user_id": str(kc_user_id) if kc_user_id else None, "email_hash": email_hash(account.email)},
                )

        if isinstance(db_exc, BaseError):
            raise

        raise BaseError(
            message="An error occurred while saving the user profile",
            code="DATABASE_ERROR",
            status_code=500,
            context={
                "email_hash": email_hash(account.email),
                "kc_user_id": str(kc_user_id) if kc_user_id else None,
                "db_error_type": type(db_exc).__name__,
            },
            cause=db_exc,
        ) from db_exc

