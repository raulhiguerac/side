import uuid
from typing import Optional

from sqlmodel import Session

from app.core.logging.utils import email_hash
from app.core.logging.logger import get_logger

from app.models.kc_tasks import KcCompensationTask, KcTaskType, KcTaskStatus
from app.services.auth.ports.identity_provider import IdentityProvider  # tu port

logger = get_logger(__name__)


def _persist_compensation_task_safe(session: Session, task: KcCompensationTask, *, log_extra: dict) -> None:
    try:
        session.add(task)
        session.commit()
        logger.info("kc_compensation_task_enqueued", extra={"extra": log_extra})
    except Exception:
        session.rollback()
        logger.exception("kc_compensation_task_persist_failed", extra={"extra": log_extra})


async def try_delete_idp_user_or_enqueue(
    *,
    session: Session,
    idp: IdentityProvider,
    kc_user_id: Optional[uuid.UUID],
    email: str,
    reason: Exception | None = None,
) -> None:
    if not kc_user_id:
        return

    extra = {"kc_user_id": str(kc_user_id), "email_hash": email_hash(email)}

    try:
        await idp.delete_account(kc_user_id)
        logger.info("idp_user_delete_succeeded", extra={"extra": extra})
        return

    except Exception as e:
        logger.error("idp_user_delete_failed", extra={"extra": extra}, exc_info=True)

        task = KcCompensationTask(
            kc_user_id=kc_user_id,
            email=email,
            task_type=KcTaskType.delete_kc_user,
            status=KcTaskStatus.pending,
            last_error=f"{type(e).__name__}: {str(e)[:500]}",
            attempts=0,
        )
        _persist_compensation_task_safe(session, task, log_extra={**extra, "reason": type(reason).__name__ if reason else None})