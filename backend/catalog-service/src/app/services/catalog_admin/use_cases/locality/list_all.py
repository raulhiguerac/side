from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.locality import (
    GetAllLocalitiesPage,
    GetAllLocalitiesRequest,
    GetAllLocalitiesResponse,
    LocalityPoint,
)


class ListLocalitiesUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, req: GetAllLocalitiesRequest) -> GetAllLocalitiesPage:
        try:
            localities = await run_in_threadpool(partial(self.uow.localities.get_all, filters=req))
            total_items = await run_in_threadpool(partial(self.uow.localities.count_all, filters=req))
        except Exception as exc:
            raise translate_db_error(exc) from exc

        items = [
            GetAllLocalitiesResponse(
                id=loc.id,
                code=loc.code,
                name=loc.name,
                locality_type=loc.locality_type,
                point=LocalityPoint(latitude=loc.latitude, longitude=loc.longitude),
                is_active=loc.is_active,
                is_capital=loc.is_capital,
            )
            for loc in localities
        ]

        return GetAllLocalitiesPage(items=items, total_items=total_items)
