import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.catalog_admin import NeighborhoodAdminNotFoundError
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.neighborhood import NeighborhoodAdminDetail


class GetNeighborhoodDetailUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, neighborhood_id: uuid.UUID) -> NeighborhoodAdminDetail:
        try:
            detail = await run_in_threadpool(
                partial(self.uow.neighborhoods.get_detail, neighborhood_id=neighborhood_id)
            )
        except Exception as exc:
            raise translate_db_error(exc) from exc

        if detail is None:
            raise NeighborhoodAdminNotFoundError(neighborhood_id=neighborhood_id)
        return detail
