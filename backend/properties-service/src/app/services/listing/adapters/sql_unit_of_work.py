from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.services.listing.adapters.sql_image_repository import SqlPropertyImageRepository
from app.services.listing.adapters.sql_location_repository import SqlPropertyLocationRepository
from app.services.listing.adapters.sql_property_repository import SqlPropertyRepository
from app.services.listing.ports.unit_of_work import ListingUnitOfWork


class SqlListingUnitOfWork(ListingUnitOfWork):
    def __init__(self, session: Session):
        self.session = session
        self._savepoint = None
        self.properties = SqlPropertyRepository(session=session)
        self.property_locations = SqlPropertyLocationRepository(session=session)
        self.property_images = SqlPropertyImageRepository(session=session)

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