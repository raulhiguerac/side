import uuid
from typing import List
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.shared.helpers.cache_keys import cache_key_localities
from app.services.geo_catalog.schemas.locality import LocalityListItem

from app.services.shared.ports.cache import CachePort
from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork

class GetLocalitiesUseCase:
    def __init__(
        self, 
        *, 
        uow: GeoCatalogUnitOfWork,
        cache_client: CachePort
    ) -> None:
        self.uow = uow
        self.cache = cache_client
    
    async def execute(
        self,
        *,
        country_id: uuid.UUID | None = None,
        admin_division_id: uuid.UUID | None = None,
    ) -> List[LocalityListItem]:
        if country_id is not None:
            cache_key = cache_key_localities(country_id=country_id)
            fetch = partial(self.uow.localities.get_active_by_country_id, country_id=country_id)
        else:
            cache_key = f"catalog:admin_division:{admin_division_id}:localities"
            fetch = partial(self.uow.localities.get_active_by_admin_division_id, admin_division_id=admin_division_id)

        try:
            cached = await self.cache.get_json(key=cache_key)
            if cached:
                return [LocalityListItem.model_validate(x) for x in cached]
        except Exception:
            pass

        localities = await run_in_threadpool(fetch)
        result = [LocalityListItem.model_validate(loc) for loc in localities]

        try:
            await self.cache.set_json(
                key=cache_key,
                value=[item.model_dump(mode="json") for item in result],
                ttl=3600 * 24,
            )
        except Exception:
            pass

        return result