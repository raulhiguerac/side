"""Fixtures para los tests de rutas.

Importar `app.main` construye el engine en tiempo de import, y `settings`
defaultea `DATABASE_PROPERTIES_URL` a `""`, que `create_engine` no sabe parsear.
La URL de acá no se conecta a nada: los tests de ruta sustituyen los use cases
por dobles, así que ninguna query llega a salir.
"""

import os

os.environ.setdefault("DATABASE_PROPERTIES_URL", "postgresql://test:test@localhost:5432/test")

import uuid  # noqa: E402
from unittest.mock import AsyncMock  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps.auth import require_admin  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.principal import Principal  # noqa: E402

ADMIN_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN = Principal(sub=ADMIN_ID, roles=["admin"])


@pytest.fixture
def admin_client():
    """TestClient con `require_admin` resuelto a un admin fijo.

    Sustituir la dependencia deja fuera la verificación real del JWT — eso es
    cosa de `deps/auth.py`, no de estas rutas. Lo que sí queda cubierto es que
    la ruta declare el principal y se lo pase al use case.
    """
    app.dependency_overrides[require_admin] = lambda: ADMIN
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def override_uc(request):
    """Reemplaza la dependencia de un use case por un `AsyncMock` y lo devuelve."""

    def _override(dependency):
        mock = AsyncMock()
        mock.execute = AsyncMock(return_value=None)
        app.dependency_overrides[dependency] = lambda: mock
        return mock

    yield _override
    app.dependency_overrides.clear()
