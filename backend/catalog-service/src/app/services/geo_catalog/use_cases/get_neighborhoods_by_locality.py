import uuid
from typing import List
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.geo_catalog.helpers.cache_keys import cache_key_neighborhoods

from app.services.geo_catalog.schemas.neighborhood import NeighborhoodListItem

from app.services.shared.ports.cache import CachePort
from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork


class GetNeighborhoodsByLocalityUseCase:
    def __init__(
        self, 
        *, 
        uow: GeoCatalogUnitOfWork,
        cache_client: CachePort
    ) -> None:
        self.uow = uow
        self.cache = cache_client

    async def execute(self, locality_id: uuid.UUID) -> List[NeighborhoodListItem]:
        cache_key = cache_key_neighborhoods(locality_id=locality_id)
        try:                                                                                               
            cached = await self.cache.get_json(key=cache_key)                                              
            if cached:                                                                                     
                return [NeighborhoodListItem.model_validate(x) for x in cached]                                
        except Exception:                                                                                  
            pass

        localities = await run_in_threadpool(
            partial(
                self.uow.neighborhoods.get_active_by_locality_id,
                locality_id=locality_id
            )
        )                 
        result = [NeighborhoodListItem.model_validate(loc) for loc in localities]
        
        try:                                                                                               
            await self.cache.set_json(                                                                     
                key=cache_key,                                                                             
                value=[item.model_dump(mode="json") for item in result],                                              
                ttl=3600 * 24                                       
            )                                                                                              
        except Exception:                                                                                  
            pass

        return result