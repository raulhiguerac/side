from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.geo_catalog import get_localities_uc
from app.services.geo_catalog.use_cases.get_locality import GetLocalitiesUseCase
from app.services.geo_catalog.schemas.locality import LocalityListItem

router = APIRouter(prefix="/localities", tags=["localities"])


@router.get("/by-country", response_model=list[LocalityListItem])
async def get_localities_by_country(
    country_id: UUID = Query(..., description="Filter by country"),
    uc: GetLocalitiesUseCase = Depends(get_localities_uc),
):
    return await uc.execute(country_id=country_id)


@router.get("/by-admin-division", response_model=list[LocalityListItem])
async def get_localities_by_admin_division(
    admin_division_id: UUID = Query(..., description="Filter by admin division"),
    uc: GetLocalitiesUseCase = Depends(get_localities_uc),
):
    return await uc.execute(admin_division_id=admin_division_id)
