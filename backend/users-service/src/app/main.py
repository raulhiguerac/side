from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.scheduler import lifespan
from app.core.logging.logger import setup_logging
from app.api.middleware.correlation_id import add_correlation_id
from app.api.handlers.exception_handlers import register_exception_handlers
from app.api.main import api_router

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Mi casa en minutos",
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    add_correlation_id(app)
    register_exception_handlers(app)

    app.include_router(api_router, prefix="/v1")
    return app

app = create_app()
