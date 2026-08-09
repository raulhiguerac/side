from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import (
    AdminPromotionSchema,
    AdminPromotionsPage,
    GetPromotionsAdminRequest,
)


class ListAllPromotionsUseCase:
    """Listado admin de promociones activas, paginado por offset.

    Sin cache a propósito. La versión anterior leía y escribía `feed_ads_global()`
    —la cache de ads del feed público— así que cambiarle la forma a la respuesta
    habría envenenado esa entrada para todos los lectores del feed. Es una lectura
    interna, de pocas filas y poco frecuente: no amerita cache propia.
    """

    def __init__(self, *, uow: AdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, request: GetPromotionsAdminRequest) -> AdminPromotionsPage:
        offset = (request.page - 1) * request.page_size

        # Secuencial y no con `gather`: comparten la Session de este UoW, que no
        # es segura entre threads.
        promotions = await run_in_threadpool(
            partial(self.uow.promotions.get_all, offset=offset, limit=request.page_size)
        )
        total = await run_in_threadpool(self.uow.promotions.count_all)

        return AdminPromotionsPage(
            items = [AdminPromotionSchema.model_validate(p) for p in promotions],
            total = total,
            page = request.page,
            page_size = request.page_size,
        )
