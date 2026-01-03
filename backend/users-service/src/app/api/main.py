from fastapi import APIRouter

from app.api.routes import account

api_router = APIRouter()
api_router.include_router(account.router)