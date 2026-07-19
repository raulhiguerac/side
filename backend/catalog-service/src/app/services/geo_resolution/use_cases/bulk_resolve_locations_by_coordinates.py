import logging
from functools import partial

import h3
from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.services.geo_resolution.ports.unit_of_work import GeoResolutionUnitOfWork
from app.services.geo_resolution.schemas.neighborhood import (
    PointToResolve,
    PointToResolveBase,
    ResolvedPoint,
)

logger = logging.getLogger(__name__)


def _enrich_with_cells(points: list[PointToResolveBase]) -> list[PointToResolve]:
    return [
        PointToResolve(
            id=p.id,
            lat=p.lat,
            lon=p.lon,
            cell=h3.latlng_to_cell(p.lat, p.lon, settings.H3_RESOLUTION),
        )
        for p in points
    ]


class BulkResolveLocationsByCoordinatesUseCase:
    def __init__(self, *, uow: GeoResolutionUnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self, *, points: list[PointToResolveBase]
    ) -> list[ResolvedPoint]:
        try:
            enriched_points = await run_in_threadpool(partial(_enrich_with_cells, points))

            return await run_in_threadpool(
                partial(self.uow.georef.get_location_by_points, points=enriched_points)
            )
        except Exception as exc:
            logger.error("bulk_resolve_locations_error count=%d reason=%s: %s", len(points), exc.__class__.__name__, exc)
            raise
