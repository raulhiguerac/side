import h3
from fastapi.concurrency import run_in_threadpool
from functools import partial

from app.core.config.settings import settings
from app.models.location import PointOfInterest
from app.services.geo_resolution.ports.routing.gateway import RoutingGateway
from app.services.shared.ports.cache import CachePort
from app.services.geo_resolution.ports.unit_of_work import GeoResolutionUnitOfWork
from app.services.geo_resolution.helpers.cache_keys import get_isochrone_key
from app.services.geo_resolution.schemas.isochrone import (
    IsochroneRequest,
    ReachablePoiItem,
    ReachablePoisResult,
)


class ResolveIsochroneUseCase:
    def __init__(
            self, 
            *, 
            uow: GeoResolutionUnitOfWork,
            cache: CachePort,
            gateway: RoutingGateway
        ) -> None:
        self.uow = uow
        self.cache = cache
        self.gateway = gateway

    async def execute(self, *, req: IsochroneRequest) -> list[ReachablePoisResult]:
        if req.property_id:
            cache_key = get_isochrone_key(property_id=req.property_id)
        else:
            h3_cell = h3.latlng_to_cell(req.lat, req.lon, settings.H3_RESOLUTION)
            cache_key = get_isochrone_key(h3_cell=h3_cell)
        
        response_json = await self.cache.get_json(key=cache_key)
        if response_json is not None:
            return [ReachablePoisResult.model_validate(entry) for entry in response_json]
        
        isochrones = await self.gateway.get_isochrones(req=req)

        models: list[dict] = []
        errors: list[ReachablePoisResult] = []
        all_cells: list[str] = []

        for entry in isochrones:
            if entry.range and entry.isochrone:
                exterior = entry.isochrone.coordinates[0]
                polygon = h3.LatLngPoly([(lat, lng) for lng, lat in exterior])
                cells = list(h3.polygon_to_cells(polygon, res=settings.H3_RESOLUTION))

                all_cells.extend(cells)

                models.append(
                    {
                        "profile": entry.profile,
                        "range": entry.range,
                        "isochrone": entry.isochrone,
                        "cells": cells,
                    }
                )
            else:
                errors.append(
                    ReachablePoisResult(
                        profile=entry.profile,
                        error="ORS did not return isochrone for this profile",
                    )
                )

        pois = await run_in_threadpool(
            partial(self.uow.pois.get_by_h3_cells, h3_cells=list(set(all_cells)))
        )
        poi_dict = self._group_pois_by_cell(pois=pois)

        response: list[ReachablePoisResult] = []

        for entry in models:
            response.append(
                ReachablePoisResult(
                    profile=entry["profile"],
                    range=entry["range"],
                    isochrone=entry["isochrone"],
                    pois=[
                        ReachablePoiItem.model_validate(poi)
                        for k in entry["cells"]
                        if k in poi_dict
                        for poi in poi_dict[k]
                    ],
                )
            )
        
        if not errors:
            await self.cache.set_json(
                key=cache_key, 
                value=[entry.model_dump(mode='json') for entry in response],
                ttl=settings.CACHE_TTL_ISOCHRONE_SECONDS
            )

        return response + errors

    @staticmethod
    def _group_pois_by_cell(*, pois: list[PointOfInterest]) -> dict[str, list[PointOfInterest]]:
        grouped: dict[str, list[PointOfInterest]] = {}

        for poi in pois:
            grouped.setdefault(poi.h3_index, []).append(poi)

        return grouped
