import uuid
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from sqlalchemy.exc import IntegrityError

from app.core.logging.utils import email_hash

from app.models.account import(
    Account,
    AccountType,
    UserProfile,
    CompanyProfile
)

from app.models.kc_tasks import (
    KcCompensationTask,
    KcTaskType,
    KcTaskStatus
)

from app.schemas.auth import AccountLogin, AccessTokenResponse, RegisterRequest
from app.repositories.account_repository import (
    get_account_by_email, 
    create_account,
    create_profile
)

from app.integrations.keycloak_admin import KeycloakAdminIntegration
from app.integrations.keycloak_auth import KeycloakAuthIntegration

from app.core.exceptions.base import BaseError
from app.core.exceptions.auth import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.core.exceptions.identity_provider import KeycloakDeleteAccountError, KeycloakSetPasswordError, IdentityProviderUnavailableError

from app.core.logging.logger import get_logger
logger = get_logger(__name__)


async def create_account_keycloak(keycloak:KeycloakAdminIntegration, account: RegisterRequest) -> uuid.UUID:

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
    
    except IdentityProviderUnavailableError as infra_exc:
        logger.error(
            "kc_user_set_password_infra_error",
            extra={"extra": {"kc_user_id": str(keycloak_uuid)}},
            exc_info=True,
        )
        raise infra_exc

    except KeycloakSetPasswordError as set_pwd_exc:
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

        raise set_pwd_exc

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

async def create_account_service(session: Session, account: RegisterRequest) -> Account:

    logger.info("db_email_check_started", extra={"extra": {"email_hash": email_hash(account.email)}})
    existing_account = get_account_by_email(session, account.email)
    logger.info("db_email_check_result", extra={"extra": {"found": bool(existing_account)}})
    if existing_account:
        raise EmailAlreadyRegisteredError(email=account.email)

    keycloak = KeycloakAdminIntegration()

    kc_user_id: uuid.UUID | None = None

    try:

        kc_user_id = await create_account_keycloak(keycloak, account)

        user_data = account.model_dump(exclude={"password"})
        new_user = Account(
            account_id=kc_user_id,
            email=user_data["email"],
            account_type=user_data["account_type"],
            onboarding_step=1
        )
        create_account(session, new_user)

        if account.account_type == AccountType.person:
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
            create_profile(session, user_profile)

        elif account.account_type == AccountType.organization:
            company_profile = CompanyProfile(
                account_id=kc_user_id,
                display_name=account.display_name,
                phone=account.phone,
                intent=getattr(account, "intent", None),
                photo_url=getattr(account, "photo_url", None),
                description=getattr(account, "description", None),
                profile_score=10
            )
            create_profile(session, company_profile)

        session.commit()
        
        logger.info("account_register_ok", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})
        return new_user
    
    except KeycloakDeleteAccountError as kc_del_exc:
        try:
            session.rollback()
        except Exception:
            logger.exception("db_rollback_failed", extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}})

        leaked_kc_user_id = None
        try:
            leaked_kc_user_id = uuid.UUID(kc_del_exc.context.get("user_id"))
        except Exception:
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

        orig = getattr(db_exc, "orig", None)
        pgcode = getattr(orig, "pgcode", None)

        constraint = getattr(orig, "diag", None)
        constraint_name = getattr(constraint, "constraint_name", None)
        column_name = getattr(constraint, "column_name", None)

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
            
            if pgcode == "23505" and constraint_name == "accounts_email_key":
                raise EmailAlreadyRegisteredError(email=account.email) from db_exc
            
            if pgcode == "23502":
                raise BaseError(
                    message=f"Missing required field: {column_name}",
                    code="MISSING_REQUIRED_FIELD",
                    status_code=400,
                    context={
                        "field": column_name,
                        "email_hash": email_hash(account.email),
                        "kc_user_id": str(kc_user_id) if kc_user_id else None,
                    },
                    cause=db_exc,
                ) from db_exc
        
            raise BaseError(
                message="Database integrity error while creating account",
                code="DATABASE_INTEGRITY_ERROR",
                status_code=500,
                context={
                    "constraint_name": constraint_name,
                    "email_hash": email_hash(account.email),
                    "kc_user_id": str(kc_user_id) if kc_user_id else None,
                },
                cause=db_exc,
            ) from db_exc

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

async def create_access_token_service(session: Session, account: AccountLogin) -> AccessTokenResponse:
    current_account = get_account_by_email(session, account.email)

    if not current_account:
        logger.info("login_unknown_email", extra={"extra": {"email_hash": email_hash(account.email)}})
        raise InvalidCredentialsError()

    if not current_account.is_active:
        logger.info("login_blocked_inactive", extra={"extra": {"email_hash": email_hash(account.email)}})
        raise InvalidCredentialsError()

    keycloak = KeycloakAuthIntegration()
    try:
        token = await run_in_threadpool(keycloak.keycloak_login, account.email, account.password)
        logger.info("account_successfully_login", extra={"extra": {"email_hash": email_hash(account.email)}})

        return AccessTokenResponse(
            access_token=token.get("access_token"),
            expires_in=token.get("expires_in"),
            refresh_token=token.get("refresh_token"),
            refresh_expires_in=token.get("refresh_expires_in"),
        )

    except InvalidCredentialsError:
        logger.info("login_invalid_password", extra={"extra": {"email_hash": email_hash(account.email)}})
        raise

    except IdentityProviderUnavailableError:
        logger.warning("account_session_infra_error", extra={"extra": {"email_hash": email_hash(account.email)}})
        raise
