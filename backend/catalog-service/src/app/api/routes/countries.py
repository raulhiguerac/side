from fastapi import APIRouter, Depends

from app.api.deps.geo_catalog import get_countries_uc
from app.services.geo_catalog.schemas.country import CountryListItem
from app.services.geo_catalog.use_cases.get_countries import GetCountriesUseCase

router = APIRouter(prefix="/countries", tags=["countries"])


@router.get("", response_model=list[CountryListItem])
async def get_active_countries(
    uc: GetCountriesUseCase = Depends(get_countries_uc),
):
    return await uc.execute()
