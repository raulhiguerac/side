from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.models.location import AdminDivision
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.admin_division import (
    AdminDivisionResponse,
    CreateAdminDivisionRequest,
)
from app.services.shared.helpers.cache_keys import cache_key_admin_division
from app.services.shared.ports.cache import CachePort


class CreateAdminDivisionUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, request: CreateAdminDivisionRequest) -> AdminDivisionResponse:
        admin_division = await run_in_threadpool(
            partial(self.uow.admin_divisions.add, admin_division=AdminDivision(**request.model_dump()))
        )

        try:
            await self.uow.commit()
            await self.uow.refresh(admin_division)
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.set_json(
                key=cache_key_admin_division(admin_division_id=admin_division.id),
                value=admin_division.model_dump(mode="json"),
                ttl=settings.CACHE_TTL_ENTITY_SECONDS,
            )
        except Exception:
            pass

        return AdminDivisionResponse.model_validate(admin_division)
