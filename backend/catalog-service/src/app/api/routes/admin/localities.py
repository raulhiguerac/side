import uuid

from fastapi import APIRouter, Depends

from app.api.deps.catalog_admin.localities import create_locality_uc, update_locality_uc
from app.services.catalog_admin.schemas.locality import (
    CreateLocalityRequest,
    LocalityAdminResponse,
    UpdateLocalityRequest,
)
from app.services.catalog_admin.use_cases.locality.create import CreateLocalityUseCase
from app.services.catalog_admin.use_cases.locality.update import UpdateLocalityUseCase

router = APIRouter()


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
