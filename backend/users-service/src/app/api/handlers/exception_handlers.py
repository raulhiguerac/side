from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import ProgrammingError
import psycopg2

from app.core.exceptions.base import BaseError

from app.core.logging.logger import get_logger

logger = get_logger(__name__)

ERROR_CODE_TO_HTTP_STATUS: dict[str, int] = {
    "MISSING_TOKEN": 401,
    "INVALID_TOKEN": 401,
    "INVALID_CREDENTIALS": 401,

    "ACCOUNT_NOT_FOUND": 404,
    "ACCOUNT_DISABLED": 403,

    "EMAIL_ALREADY_REGISTERED": 409,

    "UNSUPPORTED_FILE_TYPE": 415,
    "FILE_TOO_LARGE": 413,

    "IDENTITY_PROVIDER_UNAVAILABLE": 503,

    "IDENTITY_PROVIDER_REGISTRATION_FAILED": 502,
    "IDENTITY_PROVIDER_SET_PASSWORD_FAILED": 502,
    "IDENTITY_PROVIDER_DELETE_USER_FAILED": 502,

    "STORAGE_PROVIDER_UNAVAILABLE": 503,
    "STORAGE_UPLOAD_FAILED": 502,
    "STORAGE_ACCESS_DENIED": 403,
    "STORAGE_MISCONFIGURED": 500,
    "STORAGE_INVALID_REQUEST": 500,
    "BUCKET_NOT_FOUND": 500,
}

DEFAULT_ERROR_STATUS = 500

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseError)
    async def base_error_handler(request: Request, exc: BaseError):
        status_code = ERROR_CODE_TO_HTTP_STATUS.get(exc.code, DEFAULT_ERROR_STATUS)

        logger.warning(
            "business_error",
            extra={
                "extra": {
                    "error_code": exc.code,
                    "http_status": status_code,
                    "path": request.url.path,
                }
            },
        )

        return JSONResponse(
            status_code=status_code,
            content={
                "message": exc.message,
                "code": exc.code,
                "context": exc.context,
            },
        )

    @app.exception_handler(ProgrammingError)
    async def sqlalchemy_programming_error_handler(request: Request, exc: ProgrammingError):
        orig = getattr(exc, "orig", None)
        if isinstance(orig, psycopg2.errors.UndefinedTable):
            return JSONResponse(
                status_code=503,
                content={
                    "message": "Database schema not ready (run migrations)",
                    "code": "DB_SCHEMA_MISSING",
                },
            )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Database programming error",
                "code": "DB_PROGRAMMING_ERROR",
            },
        )
