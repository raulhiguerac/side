from fastapi import APIRouter

from app.api.routes import (
    admin,
    countries,
    geo_resolution,
    health,
    localities,
    neighborhoods,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(countries.router)
api_router.include_router(localities.router)
api_router.include_router(neighborhoods.router)
api_router.include_router(geo_resolution.router)
api_router.include_router(admin.router)
