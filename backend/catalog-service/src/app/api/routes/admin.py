import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from app.api.deps.upload_validation import validate_neighborhood_geometry_upload

from app.api.deps.auth import require_admin
from app.api.deps.catalog_admin import (
    create_country_uc,
    create_admin_division_uc,
    create_locality_uc,
    create_neighborhood_uc,
    update_country_uc,
    update_admin_division_uc,
    update_locality_uc,
    update_neighborhood_uc,
    enrich_neighborhood_geometry_uc,
)
from app.schemas.principal import Principal
from app.services.catalog_admin.use_cases.create_country import CreateCountryUseCase
from app.services.catalog_admin.use_cases.create_admin_division import CreateAdminDivisionUseCase
from app.services.catalog_admin.use_cases.create_locality import CreateLocalityUseCase
from app.services.catalog_admin.use_cases.create_neighborhood import CreateNeighborhoodUseCase
from app.services.catalog_admin.use_cases.update_country import UpdateCountryUseCase
from app.services.catalog_admin.use_cases.update_admin_division import UpdateAdminDivisionUseCase
from app.services.catalog_admin.use_cases.update_locality import UpdateLocalityUseCase
from app.services.catalog_admin.use_cases.update_neighborhood import UpdateNeighborhoodUseCase
from app.services.catalog_admin.use_cases.enrich_neighborhood_geometry import EnrichNeighborhoodGeometryUseCase
from app.services.catalog_admin.schemas.country import CreateCountryRequest, UpdateCountryRequest, CountryResponse
from app.services.catalog_admin.schemas.admin_division import CreateAdminDivisionRequest, UpdateAdminDivisionRequest, AdminDivisionResponse
from app.services.catalog_admin.schemas.locality import CreateLocalityRequest, UpdateLocalityRequest, LocalityAdminResponse
from app.services.catalog_admin.schemas.neighborhood import CreateNeighborhoodRequest, UpdateNeighborhoodRequest, NeighborhoodAdminResponse

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# -------------------------------------------------------------------------
# Countries
# -------------------------------------------------------------------------

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


# -------------------------------------------------------------------------
# Admin divisions
# -------------------------------------------------------------------------

@router.post("/admin-divisions", response_model=AdminDivisionResponse, status_code=201)
async def create_admin_division(
    body: CreateAdminDivisionRequest,
    uc: CreateAdminDivisionUseCase = Depends(create_admin_division_uc),
) -> AdminDivisionResponse:
    return await uc.execute(request=body)


@router.patch("/admin-divisions/{admin_division_id}", response_model=AdminDivisionResponse)
async def update_admin_division(
    admin_division_id: uuid.UUID,
    body: UpdateAdminDivisionRequest,
    uc: UpdateAdminDivisionUseCase = Depends(update_admin_division_uc),
) -> AdminDivisionResponse:
    return await uc.execute(admin_division_id=admin_division_id, request=body)


# -------------------------------------------------------------------------
# Localities
# -------------------------------------------------------------------------

@router.post("/localities", response_model=LocalityAdminResponse, status_code=201)
async def create_locality(
    body: CreateLocalityRequest,
    uc: CreateLocalityUseCase = Depends(create_locality_uc),
) -> LocalityAdminResponse:
    return await uc.execute(request=body)


@router.patch("/localities/{locality_id}", response_model=LocalityAdminResponse)
async def update_locality(
    locality_id: uuid.UUID,
    body: UpdateLocalityRequest,
    uc: UpdateLocalityUseCase = Depends(update_locality_uc),
) -> LocalityAdminResponse:
    return await uc.execute(locality_id=locality_id, request=body)


# -------------------------------------------------------------------------
# Neighborhoods
# -------------------------------------------------------------------------

@router.post("/neighborhoods", response_model=NeighborhoodAdminResponse, status_code=201)
async def create_neighborhood(
    body: CreateNeighborhoodRequest,
    uc: CreateNeighborhoodUseCase = Depends(create_neighborhood_uc),
) -> NeighborhoodAdminResponse:
    return await uc.execute(request=body)


@router.patch("/neighborhoods/{neighborhood_id}", response_model=NeighborhoodAdminResponse)
async def update_neighborhood(
    neighborhood_id: uuid.UUID,
    body: UpdateNeighborhoodRequest,
    uc: UpdateNeighborhoodUseCase = Depends(update_neighborhood_uc),
) -> NeighborhoodAdminResponse:
    return await uc.execute(neighborhood_id=neighborhood_id, request=body)


@router.post("/neighborhoods/{neighborhood_id}/geometry", response_model=NeighborhoodAdminResponse)
async def enrich_neighborhood_geometry(
    neighborhood_id: uuid.UUID,
    file: UploadFile,
    _: None = Depends(validate_neighborhood_geometry_upload),
    uc: EnrichNeighborhoodGeometryUseCase = Depends(enrich_neighborhood_geometry_uc),
) -> NeighborhoodAdminResponse:
    content = await file.read()
    try:
        geojson = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON file") from exc
    return await uc.execute(neighborhood_id=neighborhood_id, geojson=geojson)
