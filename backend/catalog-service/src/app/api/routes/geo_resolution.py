from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.geo_resolution import resolve_neighborhood_uc
from app.services.geo_resolution.use_cases.resolve_neighborhood import ResolveNeighborhoodUseCase
from app.services.geo_resolution.schemas.neighborhood import NeighborhoodInfo

router = APIRouter(prefix="/geo-resolution", tags=["geo-resolution"])


@router.get("/resolve-neighborhood", response_model=NeighborhoodInfo)
async def resolve_neighborhood(
    query: str = Query(..., description="Address to geocode"),
    locality_id: UUID = Query(..., description="Locality to search within"),
    uc: ResolveNeighborhoodUseCase = Depends(resolve_neighborhood_uc),
):
    return await uc.execute(query=query, locality_id=locality_id)
