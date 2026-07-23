from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.services.admin.adapters.sql_batch_repository import SqlBatchRepository
from app.services.admin.adapters.sql_property_repository import SqlAdminPropertyRepository
from app.services.admin.adapters.sql_promotion_repository import SqlPromotionRepository
from app.services.admin.ports.unit_of_work import AdminUnitOfWork

class SqlAdminUnitOfWork(AdminUnitOfWork):
    def __init__(self, session: Session) -> None:
        self.session = session
        self._savepoint = None
        self.properties = SqlAdminPropertyRepository(session=session)
        self.promotions = SqlPromotionRepository(session=session)
        self.bulk_jobs = SqlBatchRepository(session=session)

    async def commit(self) -> None:
        await run_in_threadpool(self.session.commit)

    async def rollback(self) -> None:
        await run_in_threadpool(self.session.rollback)

    async def refresh(self, instance: object) -> None:
        await run_in_threadpool(self.session.refresh, instance)
    
    async def begin_nested(self) -> None:
        self._savepoint = await run_in_threadpool(self.session.begin_nested)

    async def rollback_to_savepoint(self) -> None:
        if self._savepoint is not None:
            await run_in_threadpool(self._savepoint.rollback)
            self._savepoint = None

