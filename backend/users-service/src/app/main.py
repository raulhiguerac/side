from fastapi import FASTAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.routers import 

app = FASTAPI(
    title="Mi casa en minutos"
)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=True,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)