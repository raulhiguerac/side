import math
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.neighborhood import (
    ListNeighborhoodsAdminRequest,
    NeighborhoodAdminPage,
)


class ListNeighborhoodsUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, req: ListNeighborhoodsAdminRequest) -> NeighborhoodAdminPage:
        try:
            items = await run_in_threadpool(partial(self.uow.neighborhoods.get_all, req=req))
            total_items = await run_in_threadpool(partial(self.uow.neighborhoods.count_all, req=req))
            coverage = await run_in_threadpool(partial(self.uow.neighborhoods.get_coverage, req=req))
        except Exception as exc:
            raise translate_db_error(exc) from exc

        return NeighborhoodAdminPage(
            items=items,
            total_items=total_items,
            total_pages=math.ceil(total_items / req.page_size),
            current_page=req.page,
            items_per_page=req.page_size,
            coverage=coverage,
        )
