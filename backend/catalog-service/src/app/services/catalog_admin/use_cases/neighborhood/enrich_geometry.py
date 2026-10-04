import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.catalog_admin import (
    NeighborhoodAdminNotFoundError,
    NeighborhoodInvalidGeometryError,
)
from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.neighborhood import NeighborhoodAdminResponse
from app.services.shared.helpers.cache_keys import (
    cache_key_neighborhood,
    cache_key_neighborhoods,
)
from app.services.shared.helpers.geometry import (
    geom_from_geojson,
    geom_to_geojson,
    h3_cells_for_geojson,
)
from app.services.shared.ports.cache import CachePort


class EnrichNeighborhoodGeometryUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, neighborhood_id: uuid.UUID, geojson: dict) -> NeighborhoodAdminResponse:
        db_model = await run_in_threadpool(
            partial(self.uow.neighborhoods.get_by_id, neighborhood_id=neighborhood_id)
        )

        if not db_model:
            raise NeighborhoodAdminNotFoundError(neighborhood_id=neighborhood_id)

        geometry = geojson.get("geometry", geojson)
        geometry_type = geometry.get("type")

        if geometry_type not in ("Polygon", "MultiPolygon"):
            raise NeighborhoodInvalidGeometryError(geometry_type=geometry_type or "unknown")

        neighborhood_geometry = await run_in_threadpool(partial(geom_from_geojson, geometry))
        h3_cells = await run_in_threadpool(
            partial(h3_cells_for_geojson, geometry, resolution=settings.H3_RESOLUTION)
        )

        db_model.geom = neighborhood_geometry
        db_model.h3_cells = h3_cells

        try:
            await self.uow.commit()
            await self.uow.refresh(db_model)
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        cache_dict = db_model.model_dump(mode="json", exclude={"geom"})
        cache_dict["geom_geojson"] = geom_to_geojson(db_model.geom)

        try:
            await self.cache_client.set_json(
                key=cache_key_neighborhood(neighborhood_id=cache_dict["id"]),
                value=cache_dict,
                ttl=settings.CACHE_TTL_ENTITY_SECONDS,
            )
            await self.cache_client.delete(
                key=cache_key_neighborhoods(locality_id=cache_dict["locality_id"]),
            )
        except Exception:
            pass

        return NeighborhoodAdminResponse.model_validate(db_model)
