from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.deps.geo_resolution import (
    bulk_resolve_locations_by_coordinates_uc,
    resolve_isochrone_uc,
    resolve_location_by_coordinates_uc,
    resolve_neighborhood_uc,
    resolve_poi_uc,
)
from app.services.geo_resolution.schemas.isochrone import IsochroneRequest, ReachablePoisResult
from app.services.geo_resolution.schemas.neighborhood import (
    BulkResolveLocationsRequest,
    LocationByCoordinates,
    ResolvedNeighborhood,
    ResolvedPoint,
)
from app.services.geo_resolution.use_cases.bulk_resolve_locations_by_coordinates import (
    BulkResolveLocationsByCoordinatesUseCase,
)
from app.services.geo_resolution.use_cases.resolve_isochrone import ResolveIsochroneUseCase
from app.services.geo_resolution.use_cases.resolve_location_by_coordinates import (
    ResolveLocationByCoordinatesUseCase,
)
from app.services.geo_resolution.use_cases.resolve_neighborhood import (
    ResolveNeighborhoodUseCase,
)
from app.services.geo_resolution.use_cases.resolve_poi import ResolvePoiUseCase

router = APIRouter(prefix="/geo-resolution", tags=["geo-resolution"])


@router.get("/resolve-neighborhood", response_model=ResolvedNeighborhood)
async def resolve_neighborhood(
    background_tasks: BackgroundTasks,
    query: str = Query(..., description="Address to geocode"),
    locality_id: UUID = Query(..., description="Locality to search within"),
    uc: ResolveNeighborhoodUseCase = Depends(resolve_neighborhood_uc),
    poi_uc: ResolvePoiUseCase = Depends(resolve_poi_uc),
):
    result = await uc.execute(query=query, locality_id=locality_id)

    background_tasks.add_task(
        poi_uc.execute,
        lat=result.latitude,
        lon=result.longitude,
        locality_id=result.neighborhood.locality_id,
        neighborhood_id=result.neighborhood.id,
    )

    return result


@router.get("/by-coordinates", response_model=LocationByCoordinates)
async def resolve_location_by_coordinates(
    background_tasks: BackgroundTasks,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    poi_uc: ResolvePoiUseCase = Depends(resolve_poi_uc),
    uc: ResolveLocationByCoordinatesUseCase = Depends(resolve_location_by_coordinates_uc),
):
    result = await uc.execute(lat=lat, lon=lon)

    background_tasks.add_task(
        poi_uc.execute,
        lat=lat,
        lon=lon,
        locality_id=result.locality_id,
        neighborhood_id=result.neighborhood_id,
    )

    return result


@router.post("/by-coordinates/bulk", response_model=list[ResolvedPoint])
async def bulk_resolve_locations_by_coordinates(
    req: BulkResolveLocationsRequest,
    uc: BulkResolveLocationsByCoordinatesUseCase = Depends(bulk_resolve_locations_by_coordinates_uc),
):
    return await uc.execute(points=req.points)


@router.post("/reachable-pois", response_model=list[ReachablePoisResult])
async def reachable_pois(
    req: IsochroneRequest,
    uc: ResolveIsochroneUseCase = Depends(resolve_isochrone_uc),
):
    return await uc.execute(req=req)
