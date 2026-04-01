from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions.base import BaseError
from app.core.logging.logger import get_logger

logger = get_logger(__name__)

ERROR_CODE_TO_HTTP_STATUS: dict[str, int] = {
    # Listing
    "CREATE_PROPERTY_ERROR": 422,
    "PROPERTY_DB_UNAVAILABLE": 503,
    "INVALID_LOCATION": 422,
    "INCONSISTENT_LOCATION": 422,
    "CATALOG_SERVICE_UNAVAILABLE": 503,
    # Cache
    "CACHE_MISCONFIGURED": 500,
}

_DEFAULT_STATUS = 500


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseError)
    async def base_error_handler(request: Request, exc: BaseError):
        http_status = ERROR_CODE_TO_HTTP_STATUS.get(exc.code, _DEFAULT_STATUS)
        logger.warning(
            "business_error",
            extra={
                "extra": {
                    "error_code": exc.code,
                    "http_status": http_status,
                    "path": request.url.path,
                    "context": exc.context,
                }
            },
        )
        return JSONResponse(
            status_code=http_status,
            content={
                "message": exc.message,
                "code": exc.code,
            },
        )
