#!/bin/bash
# =============================================================================
# CREATE MICROSERVICE - DDD SCAFFOLD
# =============================================================================
#
# Crea la estructura de un microservicio siguiendo la arquitectura DDD
# usada en users-service.
#
# USO:
#   ./create_ms.sh <nombre-servicio> [dominio1] [dominio2] ...
#
# EJEMPLOS:
#   ./create_ms.sh payments-service             # Solo estructura base
#   ./create_ms.sh payments-service payment     # Con dominio "payment"
#   ./create_ms.sh listings-service listing search  # Con 2 dominios
#
# ESTRUCTURA GENERADA:
#   src/app/
#   ├── api/           → HTTP layer (routes, deps, middleware)
#   ├── core/          → Cross-cutting (config, exceptions, logging)
#   ├── integrations/  → External services (redis, keycloak, etc)
#   ├── models/        → SQLModel entities
#   ├── schemas/       → Shared Pydantic schemas
#   ├── services/      → Domain logic (ports, adapters, use_cases)
#   └── workers/       → Background jobs
#
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Argumentos
# -----------------------------------------------------------------------------

ms_name="$1"
shift
domains=("$@")  # Dominios adicionales (ej: auth, user, payment)

if [ -z "$ms_name" ]; then
  echo "❌ Error: Nombre del microservicio requerido"
  echo ""
  echo "Uso: ./create_ms.sh <nombre-servicio> [dominio1] [dominio2] ..."
  echo ""
  echo "Ejemplos:"
  echo "  ./create_ms.sh payments-service"
  echo "  ./create_ms.sh payments-service payment"
  echo "  ./create_ms.sh listings-service listing search"
  exit 1
fi

base="./$ms_name"

echo "🚀 Creando microservicio: $ms_name"
echo ""

# -----------------------------------------------------------------------------
# Estructura base: src/app/
# -----------------------------------------------------------------------------

echo "📁 Creando estructura de directorios..."

# API Layer
mkdir -p "$base/src/app/api"/{deps,handlers,http,middleware,routes}

# Core (cross-cutting concerns)
mkdir -p "$base/src/app/core"/{config,exceptions,files,logging}

# Database
mkdir -p "$base/src/app/db"

# Integrations (external services templates)
mkdir -p "$base/src/app/integrations/cache/redis/mappers"
mkdir -p "$base/src/app/integrations/storage/minio/mappers"

# Models, Schemas, Repositories
mkdir -p "$base/src/app/models"
mkdir -p "$base/src/app/schemas"
mkdir -p "$base/src/app/repositories"

# Migrations (Alembic)
mkdir -p "$base/src/app/migrations/versions"

# Utils & Workers
mkdir -p "$base/src/app/utils"
mkdir -p "$base/src/app/workers"

# Services: shared (cross-domain)
mkdir -p "$base/src/app/services/shared"/{adapters,db,helpers,policies,ports,schemas}

# -----------------------------------------------------------------------------
# Estructura de dominios específicos
# -----------------------------------------------------------------------------

for domain in "${domains[@]}"; do
  echo "   📦 Dominio: $domain"
  mkdir -p "$base/src/app/services/$domain"/{adapters,helpers,ports,schemas,services,use_cases}
done

# -----------------------------------------------------------------------------
# Tests structure
# -----------------------------------------------------------------------------

echo "🧪 Creando estructura de tests..."

# Unit tests
mkdir -p "$base/tests/unit/api"/{deps,middleware,routes}
mkdir -p "$base/tests/unit/core"
mkdir -p "$base/tests/unit/models"

# Unit tests por dominio
for domain in "${domains[@]}"; do
  mkdir -p "$base/tests/unit/services/$domain"/{helpers,services,use_cases}
done

# Integration tests
mkdir -p "$base/tests/integration"/{adapters,api,services,performance}

# Fixtures
mkdir -p "$base/tests/fixtures"

# -----------------------------------------------------------------------------
# __init__.py files
# -----------------------------------------------------------------------------

echo "📝 Creando archivos __init__.py..."

# Encontrar todos los directorios y crear __init__.py
find "$base/src" -type d -exec touch {}/__init__.py \;
find "$base/tests" -type d -exec touch {}/__init__.py \;

# -----------------------------------------------------------------------------
# Archivos base
# -----------------------------------------------------------------------------

echo "📄 Creando archivos base..."

# Main app
cat > "$base/src/app/main.py" << 'EOF'
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
EOF

# API router aggregator
cat > "$base/src/app/api/main.py" << 'EOF'
from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)

# TODO: Agregar routers de dominios
# from app.api.routes import domain
# api_router.include_router(domain.router)
EOF

# Health check route
cat > "$base/src/app/api/routes/health.py" << 'EOF'
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    return {"status": "ok"}
EOF

# Exception handlers
cat > "$base/src/app/api/handlers/exception_handlers.py" << 'EOF'
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
EOF

# Correlation ID middleware
cat > "$base/src/app/api/middleware/correlation_id.py" << 'EOF'
import uuid
from fastapi import FastAPI, Request


def add_correlation_id(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
EOF

# Base exception
cat > "$base/src/app/core/exceptions/base.py" << 'EOF'
from typing import Any, Optional


class BaseError(Exception):
    """Base exception for all domain errors."""

    def __init__(
        self,
        message: str,
        code: str,
        context: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        http_status: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.cause = cause
        self.http_status = http_status
EOF

cat > "$base/src/app/core/exceptions/__init__.py" << 'EOF'
from app.core.exceptions.base import BaseError

__all__ = ["BaseError"]
EOF

# Config settings
cat > "$base/src/app/core/config/settings.py" << 'EOF'
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    class Config:
        env_file = ".env"


settings = Settings()
EOF

# Logger
cat > "$base/src/app/core/logging/logger.py" << 'EOF'
import logging
import sys


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
EOF

# Base schema
cat > "$base/src/app/schemas/base.py" << 'EOF'
from pydantic import BaseModel, ConfigDict


class StrictBase(BaseModel):
    """Base schema with strict validation."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )
EOF

# Tests conftest
cat > "$base/tests/conftest.py" << 'EOF'
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
EOF

# Integration tests conftest placeholder
cat > "$base/tests/integration/conftest.py" << 'EOF'
"""
Integration tests fixtures.

TODO: Add fixtures for:
- test_engine (SQLite in-memory)
- test_session
- mock services (cache, email, etc)
- TestClient with dependency overrides
"""
EOF

# -----------------------------------------------------------------------------
# Config files
# -----------------------------------------------------------------------------

echo "⚙️  Creando archivos de configuración..."

# Dockerfile
cat > "$base/Dockerfile" << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# .dockerignore
cat > "$base/.dockerignore" << 'EOF'
.git
.gitignore
.env
.venv
__pycache__
*.pyc
*.pyo
.pytest_cache
.coverage
htmlcov
.mypy_cache
EOF

# .env.example
cat > "$base/.env.example" << 'EOF'
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Add service-specific env vars here
EOF

# pyproject.toml
cat > "$base/pyproject.toml" << EOF
[project]
name = "$ms_name"
version = "0.1.0"
description = "Microservice"
requires-python = ">=3.10"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "sqlmodel>=0.0.22",
    "alembic>=1.14.0",
    "psycopg2-binary>=2.9.10",
    "redis>=5.2.0",
    "uvicorn>=0.32.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
EOF

# .gitignore
cat > "$base/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
*.swp

# Environment
.env
.env.local

# Build
*.egg-info/
dist/
build/
EOF

# -----------------------------------------------------------------------------
# Inicializar proyecto con uv
# -----------------------------------------------------------------------------

echo "📦 Inicializando proyecto con uv..."

cd "$base"

# Si ya existe pyproject.toml, solo sync
if command -v uv &> /dev/null; then
  uv sync 2>/dev/null || echo "   ⚠️  uv sync falló (probablemente falta configuración)"
else
  echo "   ⚠️  uv no está instalado. Ejecuta 'uv sync' manualmente después."
fi

cd - > /dev/null

# -----------------------------------------------------------------------------
# Resumen
# -----------------------------------------------------------------------------

echo ""
echo "✅ Microservicio creado exitosamente!"
echo ""
echo "📂 Estructura:"
echo "   $base/"
echo "   ├── src/app/          → Código fuente"
echo "   │   ├── api/          → HTTP layer"
echo "   │   ├── core/         → Config, exceptions, logging"
echo "   │   ├── integrations/ → External services"
echo "   │   ├── models/       → SQLModel entities"
echo "   │   ├── services/     → Domain logic (DDD)"
echo "   │   └── ..."
echo "   └── tests/            → Unit & Integration tests"
echo ""
echo "🚀 Próximos pasos:"
echo "   1. cd $ms_name"
echo "   2. Editar .env con tus variables"
echo "   3. uv sync"
echo "   4. uv run uvicorn app.main:app --reload"
echo ""

if [ ${#domains[@]} -gt 0 ]; then
  echo "📦 Dominios creados: ${domains[*]}"
  echo "   Cada dominio tiene: adapters/, helpers/, ports/, schemas/, services/, use_cases/"
  echo ""
fi
