import uuid

from fastapi import APIRouter, Depends

from app.api.deps.catalog_admin.countries import create_country_uc, update_country_uc
from app.services.catalog_admin.schemas.country import (
    CountryResponse,
    CreateCountryRequest,
    UpdateCountryRequest,
)
from app.services.catalog_admin.use_cases.country.create import CreateCountryUseCase
from app.services.catalog_admin.use_cases.country.update import UpdateCountryUseCase

router = APIRouter()


@router.post("/countries", response_model=CountryResponse, status_code=201)
async def create_country(
    body: CreateCountryRequest,
    uc: CreateCountryUseCase = Depends(create_country_uc),
) -> CountryResponse:
    return await uc.execute(request=body)


@router.patch("/countries/{country_id}", response_model=CountryResponse)
async def update_country(
    country_id: uuid.UUID,
    body: UpdateCountryRequest,
    uc: UpdateCountryUseCase = Depends(update_country_uc),
) -> CountryResponse:
    return await uc.execute(country_id=country_id, request=body)
