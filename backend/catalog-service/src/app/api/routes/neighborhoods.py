from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.geo_catalog import (
    get_neighborhood_by_id_uc,
    get_neighborhoods_by_locality_uc,
)
from app.services.geo_catalog.schemas.neighborhood import NeighborhoodListItem
from app.services.geo_catalog.use_cases.get_neighborhood_by_id import (
    GetNeighborhoodByIdUseCase,
)
from app.services.geo_catalog.use_cases.get_neighborhoods_by_locality import (
    GetNeighborhoodsByLocalityUseCase,
)

router = APIRouter(prefix="/neighborhoods", tags=["neighborhoods"])


@router.get("/by-locality", response_model=list[NeighborhoodListItem])
async def get_neighborhoods_by_locality(
    locality_id: UUID = Query(..., description="Filter by locality"),
    uc: GetNeighborhoodsByLocalityUseCase = Depends(get_neighborhoods_by_locality_uc),
):
    return await uc.execute(locality_id=locality_id)


@router.get("/by-id", response_model=NeighborhoodListItem)
async def get_neighborhood_by_id(
    neighborhood_id: UUID = Query(..., description="Neighborhood ID"),
    uc: GetNeighborhoodByIdUseCase = Depends(get_neighborhood_by_id_uc),
):
    return await uc.execute(neighborhood_id=neighborhood_id)
