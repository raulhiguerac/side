import uuid
from typing import List
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.geo_catalog.helpers.cache_keys import cache_key_localities
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
    
    async def execute(self, country_id: uuid.UUID) -> List[LocalityListItem]:
        cache_key = cache_key_localities(country= country_id)
        try:                                                                                               
            cached = await self.cache.get_json(key=cache_key)                                              
            if cached:                                                                                     
                return [LocalityListItem.model_validate(x) for x in cached]                                
        except Exception:                                                                                  
            pass

        localities = await run_in_threadpool(
            partial(
                self.uow.localities.get_active_by_country_id,
                country_id=country_id
            )
        )                 
        result = [LocalityListItem.model_validate(loc) for loc in localities]
        
        try:                                                                                               
            await self.cache.set_json(                                                                     
                key=cache_key,                                                                             
                value=[item.model_dump() for item in result],                                              
                ttl=3600 * 24                                       
            )                                                                                              
        except Exception:                                                                                  
            pass

        return result