from app.core.config.settings import settings
import unicodedata
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.services.shared.helpers.cache_keys import cache_key_neighborhood
from app.services.shared.ports.cache import CachePort

from app.models.location import Neighborhood
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.neighborhood import CreateNeighborhoodRequest, NeighborhoodAdminResponse
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.shared.helpers.geometry import geom_to_geojson


def _normalize(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


class CreateNeighborhoodUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, request: CreateNeighborhoodRequest) -> NeighborhoodAdminResponse:
        neighborhood = await run_in_threadpool(
            partial(
                self.uow.neighborhoods.add,
                neighborhood=Neighborhood(**request.model_dump(), search_name=_normalize(request.name)),
            )
        )

        try:
            await self.uow.commit()
            await self.uow.refresh(neighborhood)
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        cache_key = cache_key_neighborhood(neighborhood_id=neighborhood.id)

        try:
            cache_dict = neighborhood.model_dump(mode="json", exclude={"geom"})
            cache_dict["geom_geojson"] = geom_to_geojson(neighborhood.geom)
            await self.cache_client.set_json(
                key=cache_key,
                value=cache_dict,
                ttl=settings.CACHE_TTL_ENTITY_SECONDS,
            )
        except Exception:
            pass

        return NeighborhoodAdminResponse.model_validate(neighborhood)
