import unicodedata
import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.catalog_admin import LocalityAdminNotFoundError
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.locality import (
    LocalityAdminResponse,
    UpdateLocalityRequest,
)
from app.services.shared.helpers.cache_keys import (
    cache_key_localities,
    cache_key_localities_by_admin_division,
    cache_key_locality,
)
from app.services.shared.ports.cache import CachePort


class UpdateLocalityUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, locality_id: uuid.UUID, request: UpdateLocalityRequest) -> LocalityAdminResponse:
        db_model = await run_in_threadpool(
            partial(self.uow.localities.get_by_id, locality_id=locality_id)
        )

        if not db_model:
            raise LocalityAdminNotFoundError(locality_id=locality_id)

        data = request.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(db_model, field, value)

        if "name" in data:
            nfkd = unicodedata.normalize("NFKD", data["name"])
            db_model.search_name = "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

        try:
            await self.uow.commit()
            await self.uow.refresh(db_model)
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.set_json(
                key=cache_key_locality(locality_id=db_model.id),
                value=db_model.model_dump(mode="json"),
                ttl=settings.CACHE_TTL_ENTITY_SECONDS,
            )
            await self.cache_client.delete(
                key=cache_key_localities(country_id=db_model.country_id),
            )
            await self.cache_client.delete(
                key=cache_key_localities_by_admin_division(admin_division_id=db_model.admin_division_id),
            )
        except Exception:
            pass

        return LocalityAdminResponse.model_validate(db_model)
