from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import ProgrammingError
import psycopg2

from app.core.exceptions.base import BaseError

from app.core.logging.logger import get_logger

logger = get_logger(__name__)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseError)
    async def base_error_handler(request: Request, exc: BaseError):
        logger.warning(
            "business_error",
            extra={
                "extra": {
                    "error_code": exc.code,
                    "path": request.url.path,
                }
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
                "code": exc.code,
                "context": exc.context,
            },
        )

    @app.exception_handler(ProgrammingError)
    async def sqlalchemy_programming_error_handler(request: Request, exc: ProgrammingError):
        # Cuando no han corrido migraciones: UndefinedTable
        orig = getattr(exc, "orig", None)
        if isinstance(orig, psycopg2.errors.UndefinedTable):
            return JSONResponse(
                status_code=503,
                content={
                    "message": "Database schema not ready (run migrations)",
                    "code": "DB_SCHEMA_MISSING",
                },
            )

        # Otros ProgrammingError (SQL inválido, etc.)
        return JSONResponse(
            status_code=500,
            content={
                "message": "Database programming error",
                "code": "DB_PROGRAMMING_ERROR",
            },
        )
