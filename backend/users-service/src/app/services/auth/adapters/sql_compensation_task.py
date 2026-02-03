from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.core.logging.logger import get_logger
from app.models.kc_tasks import KcCompensationTask, KcTaskStatus
from app.services.auth.schemas.compensation import CreateKcCompensationTask

logger = get_logger(__name__)


class SqlCompensationTaskRepository:
    def __init__(self, *, session: Session):
        self._session = session

    def _add_and_commit_sync(self, cmd: CreateKcCompensationTask) -> None:
        task = KcCompensationTask(
            kc_user_id=cmd.kc_user_id,
            email=cmd.email,
            task_type=cmd.task_type,
            status=KcTaskStatus.pending,
            last_error=cmd.last_error,
            attempts=cmd.attempts,
        )
        try:
            self._session.add(task)
            self._session.commit()
        except Exception:
            self._session.rollback()
            logger.exception(
                "kc_compensation_task_persist_failed",
                extra={"extra": {"kc_user_id": str(cmd.kc_user_id), "task_type": str(cmd.task_type)}},
            )

    async def add(self, cmd: CreateKcCompensationTask) -> None:
        await run_in_threadpool(self._add_and_commit_sync, cmd)
