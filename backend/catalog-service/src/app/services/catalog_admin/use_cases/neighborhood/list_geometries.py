from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.neighborhood import (
    ListNeighborhoodGeometriesRequest,
    NeighborhoodGeometryItem,
)


class ListNeighborhoodGeometriesUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, req: ListNeighborhoodGeometriesRequest) -> list[NeighborhoodGeometryItem]:
        try:
            return await run_in_threadpool(partial(self.uow.neighborhoods.get_geometries, req=req))
        except Exception as exc:
            raise translate_db_error(exc) from exc
