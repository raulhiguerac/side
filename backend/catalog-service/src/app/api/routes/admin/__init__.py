from fastapi import APIRouter, Depends

from app.api.deps.auth import require_admin
from app.api.routes.admin import admin_divisions, countries, localities, neighborhoods

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
router.include_router(countries.router)
router.include_router(admin_divisions.router)
router.include_router(localities.router)
router.include_router(neighborhoods.router)
