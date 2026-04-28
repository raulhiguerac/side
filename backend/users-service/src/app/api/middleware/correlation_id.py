import uuid
from fastapi import FastAPI, Request
from app.core.logging.context import request_id_ctx

def add_correlation_id(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        token = request_id_ctx.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id

        request_id_ctx.reset(token)
        return response
