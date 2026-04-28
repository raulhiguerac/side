import uuid
from functools import partial
from typing import List

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork
from app.services.geo_catalog.schemas.neighborhood import NeighborhoodListItem, NeighborhoodsByLocalityResponse
from app.services.shared.helpers.cache_keys import cache_key_neighborhoods
from app.services.shared.ports.cache import CachePort


class GetNeighborhoodsByLocalityUseCase:
    def __init__(
        self, 
        *, 
        uow: GeoCatalogUnitOfWork,
        cache_client: CachePort
    ) -> None:
        self.uow = uow
        self.cache = cache_client

    async def execute(self, locality_ids: list[uuid.UUID]) -> NeighborhoodsByLocalityResponse:
        result: dict[str, list[NeighborhoodListItem]] = {}
        missing: list[uuid.UUID] = []

        for lid in locality_ids:
            try:
                cached = await self.cache.get_json(key=cache_key_neighborhoods(locality_id=lid))
                if cached:
                    result[str(lid)] = [NeighborhoodListItem.model_validate(x) for x in cached]
                    continue
            except Exception:
                pass
            missing.append(lid)

        if not missing:
            return NeighborhoodsByLocalityResponse(neighborhoods=result)

        rows = await run_in_threadpool(
            partial(
                self.uow.neighborhoods.get_active_by_locality_ids,
                locality_ids=missing,
            )
        )

        for row in rows:
            item = NeighborhoodListItem.model_validate(row)
            key = str(row.locality_id)
            result.setdefault(key, []).append(item)

        for lid in missing:
            items = result.get(str(lid), [])
            try:
                await self.cache.set_json(
                    key=cache_key_neighborhoods(locality_id=lid),
                    value=[i.model_dump(mode="json") for i in items],
                    ttl=settings.CACHE_TTL_CATALOG_SECONDS,
                )
            except Exception:
                pass

        return NeighborhoodsByLocalityResponse(neighborhoods=result)