from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.country import (
    GetAllCountriesPage,
    GetAllCountriesRequest,
    GetAllCountriesResponse,
)


class ListCountriesUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, req: GetAllCountriesRequest) -> GetAllCountriesPage:
        try:
            countries = await run_in_threadpool(partial(self.uow.countries.get_all, filters=req))
            total_items = await run_in_threadpool(partial(self.uow.countries.count_all, filters=req))
        except Exception as exc:
            raise translate_db_error(exc) from exc

        items = [GetAllCountriesResponse.model_validate(country) for country in countries]
        return GetAllCountriesPage.build(items=items, total_items=total_items, req=req)
