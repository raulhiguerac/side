from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)

# TODO: Agregar routers de dominios
# from app.api.routes import domain
# api_router.include_router(domain.router)
