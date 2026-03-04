from sqlmodel import Session
from fastapi.concurrency import run_in_threadpool

from app.services.catalog_admin.adapters.sql_country_repository import SqlCountryRepository
from app.services.catalog_admin.adapters.sql_admin_division_repository import SqlAdminDivisionRepository
from app.services.catalog_admin.adapters.sql_locality_repository import SqlLocalityAdminRepository
from app.services.catalog_admin.adapters.sql_neighborhood_repository import SqlNeighborhoodAdminRepository
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork


class SqlCatalogAdminUnitOfWork(CatalogAdminUnitOfWork):
    def __init__(self, session: Session) -> None:
        self.session = session
        self._savepoint = None
        self.countries = SqlCountryRepository(session=session)
        self.admin_divisions = SqlAdminDivisionRepository(session=session)
        self.localities = SqlLocalityAdminRepository(session=session)
        self.neighborhoods = SqlNeighborhoodAdminRepository(session=session)

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
