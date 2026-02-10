from fastapi import APIRouter

from app.api.routes import health, localities, neighborhoods

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(localities.router)
api_router.include_router(neighborhoods.router)
