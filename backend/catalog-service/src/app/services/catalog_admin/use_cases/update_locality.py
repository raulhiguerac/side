import uuid
import unicodedata
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.shared.helpers.cache_keys import cache_key_locality, cache_key_localities
from app.services.shared.ports.cache import CachePort

from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.locality import UpdateLocalityRequest, LocalityAdminResponse
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.core.exceptions.catalog_admin import LocalityAdminNotFoundError


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

        cache_dict = db_model.model_dump(mode="json")

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.set_json(
                key=cache_key_locality(locality_id=cache_dict["id"]),
                value=cache_dict,
                ttl=3600 * 24 * 30,
            )
            await self.cache_client.delete(
                key=cache_key_localities(country_id=cache_dict["country_id"]),
            )
        except Exception:
            pass

        return LocalityAdminResponse.model_validate(cache_dict)
