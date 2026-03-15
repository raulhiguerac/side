from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.services.geo_catalog.adapters.sql_countries_repository import (
    SqlCountryRepository,
)
from app.services.geo_catalog.adapters.sql_locality_repository import (
    SqlLocalityRepository,
)
from app.services.geo_catalog.adapters.sql_neighborhood_repository import (
    SqlNeighborhoodRepository,
)
from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork


class SqlGeoCatalogUnitOfWork(GeoCatalogUnitOfWork):
    def __init__(self, session: Session):
        self.session = session
        self.countries = SqlCountryRepository(session=session)
        self.localities = SqlLocalityRepository(session=session)
        self.neighborhoods = SqlNeighborhoodRepository(session=session)
    
    async def commit(self) -> None:
        await run_in_threadpool(self.session.commit)

    async def rollback(self) -> None:
        await run_in_threadpool(self.session.rollback)