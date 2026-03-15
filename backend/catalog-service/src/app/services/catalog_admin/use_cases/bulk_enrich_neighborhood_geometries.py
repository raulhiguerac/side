import logging
import unicodedata
import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.catalog_admin.helpers.db_error_translator import translate_db_error
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.neighborhood import (
    BulkEnrichNeighborhoodGeometriesResult,
)
from app.services.shared.helpers.cache_keys import (
    cache_key_neighborhood,
    cache_key_neighborhoods,
)
from app.services.shared.helpers.geometry import geom_from_geojson
from app.services.shared.ports.cache import CachePort

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


class BulkEnrichNeighborhoodGeometriesUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, locality_id: uuid.UUID, geojson: dict, name_field: str) -> BulkEnrichNeighborhoodGeometriesResult:
        features = geojson.get("features") or []
        logger.info("bulk_enrich: locality_id=%s name_field=%s total_features=%d", locality_id, name_field, len(features))

        neighborhood_lookup: dict[str, dict] = {}
        for f in features:
            props = (f.get("properties") or {})
            raw_name = props.get(name_field)
            if not raw_name:
                continue
            normalized = _normalize(raw_name)
            if normalized not in neighborhood_lookup:
                neighborhood_lookup[normalized] = f

        logger.info("bulk_enrich: lookup built with %d unique names (sample: %s)", len(neighborhood_lookup), list(neighborhood_lookup.keys())[:5])

        if not neighborhood_lookup:
            logger.warning("bulk_enrich: no valid features found — check name_field=%s", name_field)
            return BulkEnrichNeighborhoodGeometriesResult(matched=0, unmatched=[], updated=0)

        try:
            neighborhoods = await run_in_threadpool(
                partial(
                    self.uow.neighborhoods.get_many_by_search_names,
                    locality_id=locality_id,
                    search_names=list(neighborhood_lookup.keys()),
                )
            )
        except Exception as exc:
            raise translate_db_error(exc) from exc

        logger.info("bulk_enrich: DB returned %d neighborhoods", len(neighborhoods))

        found_names = {n.search_name for n in neighborhoods}
        unmatched = [name for name in neighborhood_lookup if name not in found_names]
        logger.info("bulk_enrich: matched=%d unmatched=%d (sample unmatched: %s)", len(found_names), len(unmatched), unmatched[:5])

        if not neighborhoods:
            return BulkEnrichNeighborhoodGeometriesResult(matched=0, unmatched=unmatched, updated=0)

        updates = [
            {"id": n.id, "geom": geom_from_geojson(neighborhood_lookup[n.search_name]["geometry"])}
            for n in neighborhoods
        ]

        logger.info("bulk_enrich: executing bulk_update for %d records", len(updates))

        try:
            await run_in_threadpool(
                partial(self.uow.neighborhoods.bulk_update, neighborhoods_geom=updates)
            )
            await self.uow.commit()
            logger.info("bulk_enrich: commit ok")
        except Exception as exc:
            logger.exception("bulk_enrich: bulk_update failed")
            raise translate_db_error(exc) from exc

        keys_to_invalidate = [cache_key_neighborhood(neighborhood_id=n.id) for n in neighborhoods]
        keys_to_invalidate.append(cache_key_neighborhoods(locality_id=locality_id))
        for key in keys_to_invalidate:
            await self.cache_client.delete(key=key)

        return BulkEnrichNeighborhoodGeometriesResult(
            matched=len(neighborhoods),
            unmatched=unmatched,
            updated=len(updates),
        )
