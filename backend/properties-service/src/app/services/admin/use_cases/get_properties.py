from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import GetPropertiesAdminRequest
from app.services.shared.schemas.property_card import PropertyCardSchema


class GetPropertiesAdminUseCase:
    def __init__(self, *, uow: AdminUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, *, request: GetPropertiesAdminRequest) -> list[PropertyCardSchema]:
        offset = (request.page - 1) * request.page_size

        properties = await run_in_threadpool(
            partial(
                self.uow.properties.get_all,
                status=request.status,
                verification_status=request.verification_status,
                owner_id=request.owner_id,
                offset=offset,
                limit=request.page_size,
            )
        )

        return [PropertyCardSchema.model_validate(p) for p in properties]
