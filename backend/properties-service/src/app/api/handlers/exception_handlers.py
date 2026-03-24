from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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
                    "http_status": exc.http_status,
                    "path": request.url.path,
                }
            },
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "message": exc.message,
                "code": exc.code,
                "context": exc.context,
            },
        )
