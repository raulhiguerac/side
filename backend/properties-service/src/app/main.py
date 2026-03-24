from fastapi import FastAPI

from app.api.main import api_router
from app.api.handlers.exception_handlers import register_exception_handlers
from app.api.middleware.correlation_id import add_correlation_id
from app.core.logging.logger import setup_logging


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Service Name",  # TODO: Cambiar
        version="0.1.0",
    )

    add_correlation_id(app)
    register_exception_handlers(app)

    app.include_router(api_router, prefix="/v1")

    return app


app = create_app()
