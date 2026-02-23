import uuid
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.shared.helpers.cache_keys import cache_key_admin_division
from app.services.shared.ports.cache import CachePort

from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.admin_division import UpdateAdminDivisionRequest, AdminDivisionResponse
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.core.exceptions.catalog_admin import AdminDivisionNotFoundError


class UpdateAdminDivisionUseCase:
    def __init__(
            self,
            *,
            uow: CatalogAdminUnitOfWork,
            cache_client: CachePort,
        ) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, admin_division_id: uuid.UUID, request: UpdateAdminDivisionRequest) -> AdminDivisionResponse:
        db_model = await run_in_threadpool(
            partial(self.uow.admin_divisions.get_by_id, admin_division_id=admin_division_id)
        )

        if not db_model:
            raise AdminDivisionNotFoundError(admin_division_id=admin_division_id)

        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(db_model, field, value)

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        cache_key = cache_key_admin_division(admin_division_id=db_model.id)

        try:
            await self.cache_client.set_json(
                key=cache_key,
                value=db_model.model_dump(mode="json"),
                ttl=3600 * 24 * 30,
            )
        except Exception:
            pass

        return AdminDivisionResponse.model_validate(db_model)
