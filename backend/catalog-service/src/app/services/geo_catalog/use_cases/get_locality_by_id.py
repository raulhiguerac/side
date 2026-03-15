import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.geo_catalog import LocalityNotFoundError
from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork
from app.services.geo_catalog.schemas.locality import LocalityListItem
from app.services.shared.helpers.cache_keys import cache_key_locality
from app.services.shared.ports.cache import CachePort


class GetLocalityByIdUseCase:
    def __init__(
        self,
        *,
        uow: GeoCatalogUnitOfWork,
        cache_client: CachePort
    ) -> None:
        self.uow = uow
        self.cache = cache_client

    async def execute(self, locality_id: uuid.UUID) -> LocalityListItem:
        cache_key = cache_key_locality(locality_id=locality_id)
        try:
            cached = await self.cache.get_json(key=cache_key)
            if cached:
                return LocalityListItem.model_validate(cached)
        except Exception:
            pass

        locality = await run_in_threadpool(
            partial(
                self.uow.localities.get_active_by_id,
                locality_id=locality_id
            )
        )

        if not locality:
            raise LocalityNotFoundError(locality_id=locality_id)

        result = LocalityListItem.model_validate(locality)

        try:
            await self.cache.set_json(
                key=cache_key,
                value=result.model_dump(mode="json"),
                ttl=settings.CACHE_TTL_CATALOG_SECONDS
            )
        except Exception:
            pass

        return result