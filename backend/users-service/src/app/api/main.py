from fastapi import APIRouter

from app.api.routes import account, user

api_router = APIRouter()
api_router.include_router(account.router)
api_router.include_router(user.router)