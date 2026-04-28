import uuid
from typing import Optional

from sqlmodel import Session

from app.core.logging.utils import email_hash
from app.core.logging.logger import get_logger

from app.models.kc_tasks import KcTaskType

from app.services.auth.schemas.compensation import CreateKcCompensationTask
from app.services.auth.ports.identity_provider import IdentityProvider  # tu port

logger = get_logger(__name__)

class IdentityCompensationOrchestrator:
    def __init__(self, idp: IdentityProvider):
        self.idp = idp

    async def delete_user_or_create_compensation(
            self, 
            *,
            kc_user_id: Optional[uuid.UUID],
            email: str,
        ) -> CreateKcCompensationTask | None:


        if not kc_user_id:
            return
        
        extra = {"kc_user_id": str(kc_user_id), "email_hash": email_hash(email)}

        try:
            await self.idp.delete_account(kc_user_id)
            logger.info("idp_user_delete_succeeded", extra={"extra": extra})
            return

        except Exception as e:
            logger.error("idp_user_delete_failed", extra={"extra": extra}, exc_info=True)

            task = CreateKcCompensationTask(
                kc_user_id=kc_user_id,
                email=email,
                task_type=KcTaskType.delete_kc_user,
                last_error=f"{type(e).__name__}: {str(e)[:500]}",
            )

            return task