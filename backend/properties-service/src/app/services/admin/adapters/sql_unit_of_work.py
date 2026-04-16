from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.services.admin.adapters.sql_property_repository import SqlAdminPropertyRepository
from app.services.admin.adapters.sql_promotion_repository import SqlPromotionRepository


class SqlAdminUnitOfWork:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.properties = SqlAdminPropertyRepository(session=session)
        self.promotions = SqlPromotionRepository(session=session)

    async def commit(self) -> None:
        await run_in_threadpool(self.session.commit)

    async def rollback(self) -> None:
        await run_in_threadpool(self.session.rollback)

    async def refresh(self, instance: object) -> None:
        await run_in_threadpool(self.session.refresh, instance)
