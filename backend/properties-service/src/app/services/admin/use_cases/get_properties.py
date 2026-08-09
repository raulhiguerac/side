from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import (
    AdminPropertiesPage,
    AdminPropertyCardSchema,
    GetPropertiesAdminRequest,
)


class GetPropertiesAdminUseCase:
    def __init__(self, *, uow: AdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, request: GetPropertiesAdminRequest) -> AdminPropertiesPage:
        offset = (request.page - 1) * request.page_size
        filters = {
            "status": request.status,
            "verification_status": request.verification_status,
            "owner_id": request.owner_id,
            "is_promoted": request.is_promoted,
        }

        # Sequential, not gathered: both calls share this UoW's Session, and a
        # SQLAlchemy Session is not safe to use from two threads at once.
        properties = await run_in_threadpool(
            partial(self.uow.properties.get_all, offset=offset, limit=request.page_size, **filters)
        )
        total = await run_in_threadpool(
            partial(self.uow.properties.count_all, **filters)
        )

        return AdminPropertiesPage(
            items = [AdminPropertyCardSchema.model_validate(p) for p in properties],
            total = total,
            page = request.page,
            page_size = request.page_size,
        )
