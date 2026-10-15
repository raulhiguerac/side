from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.admin_division import (
    AdminDivisionResponse,
    GetAllAdminDivisionsPage,
    GetAllAdminDivisionsRequest,
)


class ListAdminDivisionsUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, req: GetAllAdminDivisionsRequest) -> GetAllAdminDivisionsPage:
        try:
            divisions = await run_in_threadpool(partial(self.uow.admin_divisions.get_all, filters=req))
            total_items = await run_in_threadpool(partial(self.uow.admin_divisions.count_all, filters=req))
        except Exception as exc:
            raise translate_db_error(exc) from exc

        items = [AdminDivisionResponse.model_validate(division) for division in divisions]
        return GetAllAdminDivisionsPage.build(items=items, total_items=total_items, req=req)
