import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.api.middleware.correlation_id import add_correlation_id


@pytest.fixture
def app():
    app = FastAPI()
    add_correlation_id(app)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_correlation_id_generated_when_not_provided(client):
    response = client.get("/test")

    assert response.status_code == 200
    assert "X-Request-Id" in response.headers
    # Should be a valid UUID
    request_id = response.headers["X-Request-Id"]
    uuid.UUID(request_id)  # Will raise if invalid


def test_correlation_id_preserved_when_provided(client):
    custom_id = "my-custom-request-id-123"

    response = client.get("/test", headers={"X-Request-Id": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == custom_id
