from fastapi import APIRouter

from app.api.routes import account, onboarding, user

api_router = APIRouter()
api_router.include_router(account.router)
api_router.include_router(user.router)
api_router.include_router(onboarding.router)