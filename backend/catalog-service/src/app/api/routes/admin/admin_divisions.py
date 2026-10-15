import uuid

from fastapi import APIRouter, Depends

from app.api.deps.catalog_admin.admin_divisions import (
    create_admin_division_uc,
    list_admin_divisions_uc,
    update_admin_division_uc,
)
from app.services.catalog_admin.schemas.admin_division import (
    AdminDivisionResponse,
    CreateAdminDivisionRequest,
    GetAllAdminDivisionsPage,
    GetAllAdminDivisionsRequest,
    UpdateAdminDivisionRequest,
)
from app.services.catalog_admin.use_cases.admin_division.create import (
    CreateAdminDivisionUseCase,
)
from app.services.catalog_admin.use_cases.admin_division.list_all import (
    ListAdminDivisionsUseCase,
)
from app.services.catalog_admin.use_cases.admin_division.update import (
    UpdateAdminDivisionUseCase,
)

router = APIRouter()


@router.get("/admin-divisions", response_model=GetAllAdminDivisionsPage)
async def list_admin_divisions(
    req: GetAllAdminDivisionsRequest = Depends(),
    uc: ListAdminDivisionsUseCase = Depends(list_admin_divisions_uc),
) -> GetAllAdminDivisionsPage:
    return await uc.execute(req=req)


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
