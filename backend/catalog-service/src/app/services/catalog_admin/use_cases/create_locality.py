import unicodedata
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.models.location import Locality
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.locality import (
    CreateLocalityRequest,
    LocalityAdminResponse,
)
from app.services.shared.helpers.cache_keys import (
    cache_key_localities,
    cache_key_localities_by_admin_division,
    cache_key_locality,
)
from app.services.shared.ports.cache import CachePort


def _normalize(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


class CreateLocalityUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, request: CreateLocalityRequest) -> LocalityAdminResponse:
        locality = await run_in_threadpool(
            partial(
                self.uow.localities.add,
                locality=Locality(**request.model_dump(), search_name=_normalize(request.name)),
            )
        )

        try:
            await self.uow.commit()
            await self.uow.refresh(locality)
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.set_json(
                key=cache_key_locality(locality_id=locality.id),
                value=locality.model_dump(mode="json"),
                ttl=settings.CACHE_TTL_ENTITY_SECONDS,
            )
            await self.cache_client.delete(key=cache_key_localities(country_id=request.country_id))
            await self.cache_client.delete(key=cache_key_localities_by_admin_division(admin_division_id=request.admin_division_id))
        except Exception:
            pass

        return LocalityAdminResponse.model_validate(locality)
