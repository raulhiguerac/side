import uuid
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from sqlalchemy.exc import IntegrityError

from app.core.logging.utils import email_hash

from app.models.user import(
    User,
    UserProfile,
    KcCompensationTask,
    KcTaskType,
    KcTaskStatus
)
from app.schemas.user import UserGeneric
from app.repositories.user import (
    create_user_repo, 
    create_user_profile,
    get_user_by_email
)

from app.integrations.keycloak_client import KeycloakIntegration

from app.core.exceptions.base import BaseError
from app.core.exceptions.user import EmailAlreadyRegisteredError

from app.core.logging.logger import get_logger
logger = get_logger(__name__)

async def create_user_keycloak(user: UserGeneric) -> uuid.UUID:
    keycloak = KeycloakIntegration()

    logger.info("kc_user_create_started", extra={"extra": {"email_hash": email_hash(user.email)}})

    keycloak_uuid = await run_in_threadpool(
        keycloak.create_user_record,
        user.email,
        user.name,
        user.last_name,
    )

    try:
        await run_in_threadpool(
            keycloak.set_password,
            keycloak_uuid,
            user.password,
        )
        logger.info("kc_user_create_succeeded", extra={"extra": {"kc_user_id": str(keycloak_uuid)}})
        return keycloak_uuid

    except Exception:
        logger.warning("kc_user_set_password_failed", extra={"extra": {"kc_user_id": str(keycloak_uuid)}}, exc_info=True)
        try:
            await run_in_threadpool(keycloak.delete_user, keycloak_uuid)
        except Exception:
            logger.error(
                "kc_user_delete_compensation_failed",
                extra={"extra": {"kc_user_id": str(keycloak_uuid)}},
                exc_info=True,
            )
            pass 
        raise

async def create_user_service(session: Session, user: UserGeneric) -> User:
    existing_user = get_user_by_email(session, user.email)
    if existing_user:
        raise EmailAlreadyRegisteredError(email=user.email)

    kc_user_id = await create_user_keycloak(user)

    try:
        user_data = user.model_dump(exclude={"password"})
        new_user = User(
            user_id=kc_user_id,
            email=user_data["email"],
            onboarding_step=1
        )
        create_user_repo(session, new_user)
        user_profile = UserProfile(
            user_id=kc_user_id,
            name=user.name,
            last_name=user.last_name,
            phone=user.phone,
            intent=getattr(user, "intent", None),
            photo_url=getattr(user, "photo_url", None),
            description=getattr(user, "description", None),
            profile_score=10,
        )
        create_user_profile(session, user_profile)

        session.flush()
        session.commit()

        session.refresh(new_user)
        
        logger.info("user_register_ok", extra={"extra": {"kc_user_id": str(kc_user_id)}})
        return new_user

    except IntegrityError as db_exc:
        raise EmailAlreadyRegisteredError(email=user.email) from db_exc

    except Exception as db_exc:
        logger.exception(
            "user_register_db_failed",
            extra={"extra": {"kc_user_id": str(kc_user_id), "err_type": type(db_exc).__name__}},
        )

        try:
            session.rollback()
        except Exception:
            logger.exception("db_rollback_failed", extra={"extra": {"kc_user_id": str(kc_user_id)}})

        try:
            keycloak = KeycloakIntegration()
            await run_in_threadpool(keycloak.delete_user, kc_user_id)
        except Exception as kc_exc:
            logger.exception(
                "kc_user_delete_compensation_failed",
                extra={"extra": {"kc_user_id": str(kc_user_id)}},
            )
            try:
                session.add(KcCompensationTask(
                    kc_user_id=kc_user_id,
                    email=user.email,
                    task_type=KcTaskType.delete_kc_user,
                    status=KcTaskStatus.pending,
                    last_error=type(kc_exc).__name__,
                ))
                session.commit()
                logger.warning("kc_compensation_task_created", extra={"extra": {"kc_user_id": str(kc_user_id)}})
            except Exception:
                logger.exception("kc_compensation_task_persist_failed", extra={"extra": {"kc_user_id": str(kc_user_id)}})
                try:
                    session.rollback()
                except Exception:
                    logger.exception("db_rollback_failed", extra={"extra": {"kc_user_id": str(kc_user_id)}})

        if isinstance(db_exc, BaseError):
            raise

        raise BaseError(
            message="An error occurred while saving the user profile",
            code="DATABASE_ERROR",
            status_code=500,
            context={
                "email_hash": email_hash(user.email),
                "kc_user_id": str(kc_user_id),
                "db_error_type": type(db_exc).__name__,
            },
            cause=db_exc,
        ) from db_exc

