from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.deps.geo_resolution import resolve_neighborhood_uc, resolve_poi_uc
from app.services.geo_resolution.use_cases.resolve_neighborhood import ResolveNeighborhoodUseCase
from app.services.geo_resolution.use_cases.resolve_poi import ResolvePoiUseCase
from app.services.geo_resolution.schemas.neighborhood import ResolvedNeighborhood

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
