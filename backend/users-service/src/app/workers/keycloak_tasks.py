import asyncio
from sqlmodel import Session, select
from datetime import datetime, timedelta
import random

from keycloak.exceptions import KeycloakGetError

from app.models.kc_tasks import KcCompensationTask, KcTaskStatus
from app.integrations.keycloak_admin import KeycloakAdminIntegration

from sqlmodel import Session
from app.api.deps.db import engine


from app.core.logging.logger import get_logger
logger = get_logger(__name__)

MAX_ATTEMPTS = 5
BATCH_SIZE = 25
MAX_DELAY_MIN = 60


async def run_job() -> None:
    await asyncio.to_thread(_run_job_sync)

def _run_job_sync() -> None:
    with Session(engine) as session:
        retry_keycloak_deletions(session)

def retry_keycloak_deletions(session: Session):

    tasks = session.exec(
        select(KcCompensationTask)
        .where(KcCompensationTask.status == KcTaskStatus.pending)
        .where(KcCompensationTask.attempts < MAX_ATTEMPTS)
        .where(KcCompensationTask.next_retry_at <= datetime.utcnow())
        .limit(BATCH_SIZE)
    ).all()

    logger.info("start_compensation_task", extra={"extra": {"count": len(tasks)}})

    if len(tasks) == 0:
        logger.info("no_compensation_task_to_run")
        return

    keycloak = KeycloakAdminIntegration()

    for task in tasks:

        try:
            keycloak.delete_account(task.kc_user_id)
            task.status = KcTaskStatus.done
            task.last_error = None

            logger.info(
                "kc_user_deleted_successfully",
                extra={"extra": {"task_id": str(task.id), "kc_user": str(task.kc_user_id)}},
            )

        except Exception as e:
            task.attempts += 1
            task.last_error = f"{type(e).__name__}: {str(e)[:500]}"  # truncado

            delay_min = min(MAX_DELAY_MIN, 2 ** task.attempts)
            jitter_sec = random.randint(0, 30)
            task.next_retry_at = datetime.utcnow() + timedelta(minutes=delay_min, seconds=jitter_sec)

            # opcional: si attempts llegó al máximo, márcala failed
            if task.attempts >= MAX_ATTEMPTS:
                task.status = KcTaskStatus.failed  # si tienes ese enum

            logger.warning(
                "kc_user_deleted_fail",
                exc_info=True,
                extra={"extra": {
                    "task_id": str(task.id),
                    "kc_user": str(task.kc_user_id),
                    "attempts": task.attempts,
                    "next_retry_at": task.next_retry_at.isoformat(),
                    "error_type": type(e).__name__,
                }},
            )
        
        try:
            session.add(task)
            session.commit()
        except Exception as db_err:
            session.rollback()
            logger.error(
                "Failed to update task",
                extra={"extra": {"task_id": str(task.id), "db_err": db_err}},
            )
