import uuid
from datetime import datetime, timedelta, timezone
from functools import partial

import h3
from fastapi.concurrency import run_in_threadpool

from app.models.location import FetchZone
from app.services.shared.ports.cache import CachePort
from app.services.geo_resolution.ports.unit_of_work import GeoResolutionUnitOfWork
from app.services.geo_resolution.ports.poi_provider_gateway import PoiProviderGateway
from app.services.geo_resolution.helpers.cache_keys import (
    cache_key_fetch_zone,
    lock_key_fetch_zone,
)

STALE_THRESHOLD_DAYS = 30
LOCK_TTL_SECONDS = 30


class ResolvePoiUseCase:
    """
    Populate-on-demand: DB local → Overpass API → persist.

    Fire-and-forget: se invoca como side-effect del resolve neighborhood.
    No devuelve datos, solo pobla la DB con POIs para la celda H3.
    """

    def __init__(
        self,
        *,
        uow: GeoResolutionUnitOfWork,
        cache_client: CachePort,
        poi_provider: PoiProviderGateway,
    ):
        self.uow = uow
        self.cache_client = cache_client
        self.poi_provider = poi_provider

    @staticmethod
    def _h3_to_bbox(h3_index: str) -> list[float]:
        coords = h3.cell_to_boundary(h3_index)
        lats = [c[0] for c in coords]
        lngs = [c[1] for c in coords]
        return [min(lats), min(lngs), max(lats), max(lngs)]

    async def execute(
        self,
        *,
        lat: float,
        lon: float,
        locality_id: uuid.UUID,
        neighborhood_id: uuid.UUID,
    ) -> None:
        h3_index = h3.latlng_to_cell(lat, lon, res=9)

        cache_key = cache_key_fetch_zone(h3_index=h3_index)
        cached = await self.cache_client.get(key=cache_key)
        if cached:
            return

        lock_key = lock_key_fetch_zone(h3_index=h3_index)
        acquired = await self.cache_client.set_nx(
            key=lock_key, value="1", ttl=LOCK_TTL_SECONDS,
        )
        if not acquired:
            return

        try:
            fetched_zone = await run_in_threadpool(
                partial(self.uow.fetch_zones.get_by_h3_index, h3_index=h3_index)
            )

            if fetched_zone:
                fresh_until = fetched_zone.fetched_at + timedelta(days=STALE_THRESHOLD_DAYS)
                remaining = int((fresh_until - datetime.now(timezone.utc)).total_seconds())

                if remaining > 0:
                    await self._set_cache(key=cache_key, ttl=remaining)
                    return

                fetched_zone.is_stale = True
                await self.uow.commit()
                return

            bbox = self._h3_to_bbox(h3_index)
            pois = await self.poi_provider.get_pois_by_bbox(
                bbox=bbox,
                locality_id=locality_id,
                neighborhood_id=neighborhood_id,
                h3_index=h3_index,
            )

            await run_in_threadpool(
                partial(self.uow.pois.add_many, pois=pois)
            )
            await run_in_threadpool(
                partial(
                    self.uow.fetch_zones.add,
                    fetch_zone=FetchZone(
                        locality_id=locality_id,
                        h3_index=h3_index,
                        poi_count=len(pois),
                        fetched_at=datetime.now(timezone.utc),
                    ),
                )
            )

            await self.uow.commit()
            await self._set_cache(key=cache_key, ttl=STALE_THRESHOLD_DAYS * 86400)

        except Exception:
            await self.uow.rollback()
        finally:
            await self.cache_client.delete(key=lock_key)

    async def _set_cache(self, *, key: str, ttl: int) -> None:
        try:
            await self.cache_client.set(key=key, value="1", ttl=ttl)
        except Exception:
            pass
