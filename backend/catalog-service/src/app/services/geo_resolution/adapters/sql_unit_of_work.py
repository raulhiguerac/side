from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.services.geo_resolution.adapters.sql_fetch_zone_repository import (
    SqlFetchZoneRepository,
)
from app.services.geo_resolution.adapters.sql_georeferentiation_repository import (
    SqlGeoreferentiationRepository,
)
from app.services.geo_resolution.adapters.sql_poi_repository import SqlPoiRepository
from app.services.geo_resolution.ports.unit_of_work import GeoResolutionUnitOfWork


class SqlGeoResolutionUnitOfWork(GeoResolutionUnitOfWork):
    """Adapter SQL para GeoResolutionUnitOfWork."""
    def __init__(self, session: Session):
        self.session = session
        self.pois = SqlPoiRepository(session=session)
        self.fetch_zones = SqlFetchZoneRepository(session=session)
        self.georef = SqlGeoreferentiationRepository(session=session)
    
    async def commit(self) -> None:
        await run_in_threadpool(self.session.commit)

    async def rollback(self) -> None:
        await run_in_threadpool(self.session.rollback)