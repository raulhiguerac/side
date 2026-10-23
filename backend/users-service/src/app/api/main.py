from fastapi import APIRouter

from app.api.routes import auth, health, onboarding
from app.api.routes.user import account, profile

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(account.router)
api_router.include_router(profile.router)
api_router.include_router(onboarding.router)
