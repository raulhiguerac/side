from fastapi import APIRouter

from app.api.routes import health
from app.api.routes import admin, properties, search

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(properties.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)
