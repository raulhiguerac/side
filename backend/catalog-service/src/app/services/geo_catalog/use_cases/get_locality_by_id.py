import uuid
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.geo_catalog.helpers.cache_keys import cache_key_locality

from app.models.location import Locality
from app.core.exceptions.geo_catalog import LocalityNotFoundError

from app.services.shared.ports.cache import CachePort
from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork

class GetLocalityByIdUseCase:
    def __init__(
        self, 
        *, 
        uow: GeoCatalogUnitOfWork,
        cache_client: CachePort
    ) -> None:
        self.uow = uow
        self.cache = cache_client
    
    async def execute(self, locality_id: uuid.UUID) -> Locality:
        cache_key = cache_key_locality(locality_id=locality_id)
        try:                                                                                               
            cached = await self.cache.get_json(key=cache_key)                                              
            if cached:                                                                                     
                return Locality.model_validate(cached)
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

        try:                                                                                               
            await self.cache.set_json(                                                                     
                key=cache_key,                                                                             
                value=locality.model_dump(mode="json"),                                              
                ttl=3600 * 24                                       
            )                                                                                              
        except Exception:                                                                                  
            pass

        return locality