"""
=============================================================================
CONFTEST PARA TESTS DE INTEGRACION
=============================================================================

Este archivo contiene los "fixtures" - piezas reutilizables que preparan
el entorno para los tests. Piensa en ellos como los ingredientes que
necesitas antes de cocinar.

CONCEPTOS CLAVE:
----------------
1. FIXTURE: Una funcion que prepara algo que el test necesita
   - Se usa con el decorador @pytest.fixture
   - pytest automaticamente la ejecuta antes del test que la necesite

2. SCOPE: Cuanto tiempo vive el fixture
   - "function": Se crea nuevo para CADA test (default)
   - "module": Se crea una vez por archivo de tests
   - "session": Se crea una vez para TODOS los tests

3. YIELD vs RETURN:
   - return: Solo devuelve el valor
   - yield: Devuelve el valor Y permite hacer cleanup despues del test

4. DEPENDENCY OVERRIDE:
   - FastAPI permite reemplazar dependencias (ej: base de datos real)
     por versiones de prueba (ej: base de datos en memoria)
"""

import sys
from pathlib import Path

# =============================================================================
# PASO 0: Agregar src/ al path para que Python encuentre el modulo 'app'
# =============================================================================
# Esto es necesario porque el codigo fuente esta en src/app/
# y Python no lo encuentra automaticamente desde tests/

src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import os
import uuid
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# -----------------------------------------------------------------------------
# PASO 1: Configurar variables de entorno ANTES de importar la app
# -----------------------------------------------------------------------------
# Algunas dependencias (como auth.py) leen variables de entorno al importarse.
# Por eso las configuramos primero con valores "fake" para testing.

os.environ.setdefault("DATABASE_URL", "sqlite://")  # Se sobreescribe despues
os.environ.setdefault("KC_JWKS_URL", "http://fake-keycloak/jwks")
os.environ.setdefault("KC_ISSUER", "http://fake-keycloak/realm")
os.environ.setdefault("OIDC_AUDIENCE", "test-audience")
os.environ.setdefault("FRONT_BASE_URL", "http://localhost:3000")

# Ahora si podemos importar la app y sus dependencias
from app.main import create_app
from app.api.deps.db import get_session
from app.api.deps.auth import get_current_principal
from app.api.deps.auth_use_cases import (
    get_identity_provider,
    get_auth_provider,
    get_cache_port as get_auth_cache_port,
    get_email_sender as get_auth_email_sender,
)
from app.api.deps.user_use_cases import (
    get_cache_port as get_user_cache_port,
    get_email_sender as get_user_email_sender,
)
from app.schemas.common import Principal
from app.services.auth.schemas.tokens import AuthTokens


# =============================================================================
# FIXTURES DE BASE DE DATOS
# =============================================================================


@pytest.fixture(scope="function")
def test_engine():
    """
    Crea un motor de base de datos SQLite EN MEMORIA.

    Por que SQLite en memoria?
    - Es rapido (no escribe a disco)
    - Es aislado (cada test tiene su propia DB)
    - No necesita setup externo (no PostgreSQL, no Docker)

    StaticPool: Mantiene una sola conexion para evitar problemas
    con SQLite y multithreading.

    check_same_thread=False: Permite usar la conexion desde diferentes threads
    (necesario porque FastAPI usa async).

    NOTA IMPORTANTE SOBRE SQLite Y UUIDs:
    ------------------------------------
    SQLite no soporta UUIDs nativamente. SQLAlchemy intenta convertirlos
    usando .hex pero esto falla si el valor ya es un string.

    Para tests de integracion REALES en produccion, usar PostgreSQL
    con testcontainers. SQLite es solo para demos/desarrollo rapido.
    """
    from sqlalchemy import event
    import uuid as uuid_module

    engine = create_engine(
        "sqlite://",  # :memory: database
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Registrar adaptador para convertir UUIDs a strings en SQLite
    # Esto es necesario porque SQLite no tiene tipo UUID nativo
    import sqlite3
    sqlite3.register_adapter(uuid_module.UUID, lambda u: str(u))

    # Crear todas las tablas definidas en los modelos SQLModel
    SQLModel.metadata.create_all(engine)

    yield engine

    # Cleanup: eliminar tablas despues del test
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_engine) -> Generator[Session, None, None]:
    """
    Crea una sesion de base de datos conectada al engine de prueba.

    Esta sesion es lo que usaran los repositorios para hacer queries.

    El patron "yield" permite:
    1. Crear la sesion
    2. Darsela al test (yield)
    3. Cerrarla cuando el test termine (despues del yield)
    """
    with Session(test_engine) as session:
        yield session


# =============================================================================
# MOCKS DE SERVICIOS EXTERNOS
# =============================================================================
# En integracion, queremos probar que TODO funciona junto, EXCEPTO
# servicios externos como Keycloak, Redis, etc. Esos los "mockeamos".


@pytest.fixture
def mock_identity_provider():
    """
    Mock del Identity Provider (Keycloak Admin API).

    Este servicio se encarga de:
    - Crear usuarios en Keycloak
    - Cambiar contrasenas
    - Eliminar usuarios

    AsyncMock: Porque los metodos son async (usan await)

    IMPORTANTE: create_account debe devolver un uuid.UUID (no string)
    porque el UC usa ese valor como account_id en la DB.
    """
    mock = AsyncMock()

    # Configurar comportamiento por defecto
    # create_account devuelve un UUID objeto (NO string!)
    # El UC usa este valor como account_id en la base de datos
    mock.create_account.return_value = uuid.uuid4()
    mock.change_password.return_value = None
    mock.delete_account.return_value = None

    return mock


@pytest.fixture
def mock_auth_provider():
    """
    Mock del Authentication Provider (Keycloak OIDC).

    Este servicio se encarga de:
    - Login (email + password -> tokens)
    - Refresh token
    - Logout (invalidar session)

    Los tokens que devolvemos son "fake" pero tienen la estructura correcta.
    """
    mock = AsyncMock()

    # Login exitoso devuelve tokens
    mock.login.return_value = AuthTokens(
        access_token="fake-access-token",
        refresh_token="fake-refresh-token",
        expires_in=3600,  # 1 hora
        refresh_expires_in=86400,  # 24 horas
    )

    # Refresh devuelve nuevos tokens
    mock.refresh_token.return_value = AuthTokens(
        access_token="fake-new-access-token",
        refresh_token="fake-new-refresh-token",
        expires_in=3600,
        refresh_expires_in=86400,
    )

    # Logout no devuelve nada
    mock.logout.return_value = None

    return mock


@pytest.fixture
def mock_cache():
    """
    Mock del servicio de cache (Redis).

    Se usa para:
    - Guardar tokens temporales (reset password, reactivacion)
    - Rate limiting
    - Cache de datos frecuentes
    """
    mock = AsyncMock()
    mock.get.return_value = None  # Por defecto no hay nada en cache
    mock.set.return_value = None
    mock.delete.return_value = None
    return mock


@pytest.fixture
def mock_email_sender():
    """
    Mock del servicio de email (Brevo/Sendinblue).

    Se usa para enviar emails de:
    - Reset de password
    - Reactivacion de cuenta
    - Verificacion de email
    """
    mock = AsyncMock()
    mock.send_template_email.return_value = None
    return mock


# =============================================================================
# FIXTURE PARA AUTENTICACION
# =============================================================================


@pytest.fixture
def authenticated_principal():
    """
    Crea un "Principal" - representa un usuario autenticado.

    En produccion, esto viene del JWT token en las cookies.
    En tests, lo inyectamos directamente para simular un usuario logueado.

    Campos:
    - sub: Subject (ID del usuario) - es un UUID
    - email: Email del usuario
    - email_verified: Si el email esta verificado
    - scope: Permisos/roles del usuario
    """
    return Principal(
        sub=uuid.uuid4(),  # Se sobreescribe en cada test si es necesario
        email="test@example.com",
        email_verified=True,
        scope=[],
    )


# =============================================================================
# FIXTURE PRINCIPAL: TEST CLIENT
# =============================================================================


@pytest.fixture
def client(
    test_session: Session,
    mock_identity_provider,
    mock_auth_provider,
    mock_cache,
    mock_email_sender,
) -> Generator[TestClient, None, None]:
    """
    Crea el TestClient de FastAPI con todas las dependencias reemplazadas.

    DEPENDENCY OVERRIDE EXPLICADO:
    ------------------------------
    FastAPI usa "Dependency Injection" - las funciones declaran que necesitan
    (ej: get_session) y FastAPI se las da automaticamente.

    dependency_overrides nos permite decir:
    "Cuando alguien pida get_session, dale test_session en su lugar"

    Esto nos permite:
    1. Usar base de datos de prueba en lugar de produccion
    2. Usar mocks en lugar de servicios reales (Keycloak, Redis, etc)

    IMPORTANTE: TestClient es SINCRONO aunque la app sea async.
    Internamente maneja la conversion.
    """
    # Crear una nueva instancia de la app para este test
    app = create_app()

    # --- OVERRIDE 1: Base de datos ---
    # Reemplazar la sesion de produccion por la de prueba
    def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    # --- OVERRIDE 2: Identity Provider (Keycloak Admin) ---
    app.dependency_overrides[get_identity_provider] = lambda: mock_identity_provider

    # --- OVERRIDE 3: Auth Provider (Keycloak OIDC) ---
    app.dependency_overrides[get_auth_provider] = lambda: mock_auth_provider

    # --- OVERRIDE 4: Cache (Redis) - hay dos funciones get_cache_port! ---
    # Una en auth_use_cases y otra en user_use_cases
    app.dependency_overrides[get_auth_cache_port] = lambda: mock_cache
    app.dependency_overrides[get_user_cache_port] = lambda: mock_cache

    # --- OVERRIDE 5: Email Sender (Brevo) - tambien hay dos! ---
    app.dependency_overrides[get_auth_email_sender] = lambda: mock_email_sender
    app.dependency_overrides[get_user_email_sender] = lambda: mock_email_sender

    # Crear el cliente de prueba
    with TestClient(app) as test_client:
        yield test_client

    # Limpiar los overrides despues del test
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(
    client: TestClient,
    authenticated_principal: Principal,
) -> TestClient:
    """
    TestClient con un usuario ya autenticado.

    Util para tests que requieren estar logueado (GET /users/me, etc).

    En lugar de hacer login real, simplemente inyectamos el Principal
    directamente, saltandonos la validacion del JWT.
    """
    # Obtener la app del client
    app = client.app

    # Override: cuando pidan get_current_principal, dar nuestro principal fake
    app.dependency_overrides[get_current_principal] = lambda: authenticated_principal

    return client


# =============================================================================
# HELPERS PARA TESTS
# =============================================================================


@pytest.fixture
def person_register_data():
    """Datos de registro para una persona (usuario individual)."""
    return {
        "first_name": "Pepito",
        "last_name": "Perez",
        "email": "pepito@example.com",
        "password": "SecurePassword123!",
        "phone": "3001234567",
        "account_type": "person",
    }


@pytest.fixture
def organization_register_data():
    """Datos de registro para una organizacion (empresa)."""
    return {
        "display_name": "Mi Empresa SAS",
        "email": "empresa@example.com",
        "password": "SecurePassword123!",
        "phone": "6011234567",
        "account_type": "organization",
    }


@pytest.fixture
def login_data():
    """Datos para hacer login."""
    return {
        "email": "pepito@example.com",
        "password": "SecurePassword123!",
    }
