from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions.base import BaseError
from app.core.logging.logger import get_logger

logger = get_logger(__name__)

ERROR_CODE_TO_HTTP_STATUS: dict[str, int] = {
    # geo_catalog
    "LOCALITY_NOT_FOUND": 404,
    "NEIGHBORHOOD_NOT_FOUND": 404,
    # geo_resolution
    "GEO_RESOLUTION_MISCONFIGURED": 503,
    "GEO_RESOLUTION_UNAVAILABLE": 503,
    "GEO_RESOLUTION_BAD_REQUEST": 400,
    "GEO_RESOLUTION_NOT_FOUND": 404,
    "NEIGHBORHOOD_RESOLUTION_NOT_FOUND": 404,
    # catalog_admin — not found
    "COUNTRY_NOT_FOUND": 404,
    "ADMIN_DIVISION_NOT_FOUND": 404,
    "LOCALITY_ADMIN_NOT_FOUND": 404,
    "NEIGHBORHOOD_ADMIN_NOT_FOUND": 404,
    # catalog_admin — conflict
    "COUNTRY_CONFLICT": 409,
    "ADMIN_DIVISION_CONFLICT": 409,
    "LOCALITY_CONFLICT": 409,
    "NEIGHBORHOOD_CONFLICT": 409,
    # catalog_admin — infra
    "CATALOG_ADMIN_DB_UNAVAILABLE": 503,
    # auth
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
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
