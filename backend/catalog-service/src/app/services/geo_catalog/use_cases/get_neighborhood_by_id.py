import uuid
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.geo_catalog.helpers.cache_keys import cache_key_neighborhood

from app.models.location import Neighborhood
from app.core.exceptions.geo_catalog import NeighborhoodNotFoundError

from app.services.shared.ports.cache import CachePort
from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork


class GetNeighborhoodByIdUseCase:
    def __init__(
        self,
        *,
        uow: GeoCatalogUnitOfWork,
        cache_client: CachePort
    ) -> None:
        self.uow = uow
        self.cache = cache_client

    async def execute(self, neighborhood_id: uuid.UUID) -> Neighborhood:
        cache_key = cache_key_neighborhood(neighborhood_id=neighborhood_id)
        try:
            cached = await self.cache.get_json(key=cache_key)
            if cached:
                return Neighborhood.model_validate(cached)
        except Exception:
            pass

        neighborhood = await run_in_threadpool(
            partial(
                self.uow.neighborhoods.get_active_by_id,
                neighborhood_id=neighborhood_id
            )
        )

        if not neighborhood:
            raise NeighborhoodNotFoundError(neighborhood_id=neighborhood_id)

        try:
            await self.cache.set_json(
                key=cache_key,
                value=neighborhood.model_dump(mode="json"),
                ttl=3600 * 24
            )
        except Exception:
            pass

        return neighborhood
