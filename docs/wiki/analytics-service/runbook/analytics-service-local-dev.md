---
title: Runbook — analytics-service local dev
status: stable
last-verified: 2026-09-07
owners: [analytics-service]
related:
  - "[[analytics-service]]"
  - "[[analytics-service-architecture]]"
  - "[[avm-training]]"
  - "[[adr-mlflow-minio-stack]]"
sources:
  - ../../../sources/analytics-service/2026-05-19-foundational-qa.md
  - ../../../sources/analytics-service/2026-05-20-prediction-wiring-and-batch-uc.md
  - ../../../sources/analytics-service/2026-05-25-worker-wiring-fixes.md
  - ../../../sources/analytics-service/2026-05-25-unit-test-suite.md
  - ../../../sources/_shared/2026-09-07-entorno-dev-migrable.md
---

## TL;DR

> **Actualizado 2026-09-07 — el arranque ya no es manual.** `make bootstrap && make up`
> levanta los 21 servicios, aplica migraciones y siembra datos. Este runbook queda
> como referencia de los detalles internos del servicio y de como correrlo a mano
> cuando lo estas debuggeando. Ver [`README.md`](README.md) para el flujo normal.

Flujo: abrir el repo en VS Code → "Reopen in Container" → docker-compose levanta toda la infra (Postgres por servicio + Keycloak + Redis + MinIO + MLflow). Después, **a mano**: `cd backend/analytics-service && uv sync && PYTHONPATH=src uv run uvicorn app.main:app --reload --port 8000`.

El servicio analytics **no está como service en el compose** — se corre manual dentro del devcontainer.

## Prerequisites

- Docker Desktop (o engine equivalente) corriendo.
- VS Code con la extensión **Dev Containers** (`ms-vscode-remote.remote-containers`).
- Repo clonado, `.env.local` completado y `make bootstrap` corrido.
- `.env.local` completado (7 valores) y `make bootstrap` corrido.

## Levantar el entorno

1. Abrir el repo en VS Code.
2. Command palette → **Dev Containers: Reopen in Container**.
3. Primera vez compila el devcontainer + arranca todos los services. Tarda ~5–10 min.
4. Al conectar al devcontainer, el `postCreateCommand` corre [data/ml/AVM/scripts/setup-analytics-kernel.sh](data/ml/AVM/scripts/setup-analytics-kernel.sh):
   - `uv sync` sobre analytics-service.
   - Registra un Jupyter kernel llamado `analytics` (para EDA del data team desde el mismo devcontainer).

## Servicios que levantan automáticamente

| Servicio | Imagen | Host port | Para qué | Credenciales |
|---|---|---|---|---|
| `develop` | build local | 8000, 5173, 8080 | El devcontainer (tu shell) | n/a |
| `users-ms-db` | postgres:17 | (interno) | DB de users-service | admin / admin |
| `catalog-ms-db` | postgis/postgis:17-master | (interno) | DB de catalog-service | admin / admin |
| `properties-ms-db` | postgis/postgis:17-master | (interno) | DB de properties-service | admin / admin |
| `analytics-ms-db` | postgres:17 | (interno) | DB de analytics-service — `POSTGRES_DB: analytics-ms-db` | admin / admin |
| `keycloak-db` | postgres:17 | (interno) | DB de Keycloak | keycloak / password |
| `keycloak` | keycloak:26.4.7 | **8180** | IdP — admin UI en http://localhost:8180 | admin / admin |
| `redis` | redis:latest | 6379 | Cache + rate limit | n/a |
| `redisinsight` | redis/redisinsight | 5540 | UI de Redis — http://localhost:5540 | n/a |
| `minio` | minio/minio:RELEASE.2025-09-07T16-13-09Z-cpuv1 | 9000 (API), **9001** (console) | Artifact store — console en http://localhost:9001 | minioadmin / minioadmin |
| `mlflow` | mlflow:v3.12.0-full | 5000 | Model registry + tracking — UI en http://localhost:5000 | n/a |
| `kafka-broker` | apache/kafka:latest | 9092 | Broker Kafka — `advertised.listeners` interno `broker:29092` | n/a |
| `topic-init` | apache/kafka:latest | — | One-shot: crea los topics `listing-created`, `price-predicted`, `listing-created-dlq` | n/a |
| `router` | openrouteservice/openrouteservice:nightly | 8082 | ORS — usado por catalog-service, no por analytics | n/a |

`analytics-ms-db` **ya existe** en el compose (agregado antes del 2026-05-25) — 14 services en total, no 10. El worker Kafka necesita que `kafka-broker` y `topic-init` estén up para conectar; eso no está documentado en la sección "Correr analytics-service" más abajo.

## Correr analytics-service

Dentro del devcontainer:

```bash
cd /workspace/backend/analytics-service
uv sync
# el .env.dev del servicio ya viene versionado; no hay que crearlo

# API web
PYTHONPATH=src uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Worker Kafka (proceso separado)
PYTHONPATH=src uv run python src/app/workers/listing_created/runner.py
```

`PYTHONPATH=src` es obligatorio para el src-layout — sin esto `import app` falla. El Dockerfile lo setea como `ENV PYTHONPATH=/app/src`.

Health check:
```bash
curl http://localhost:8000/v1/health
```

## Env vars del servicio

`backend/analytics-service/.env.example` **está incompleto** al 2026-05-20: solo declara `DATABASE_URL` y `REDIS_URL`. Para que `/predict` funcione, el `.env` real necesita además las 5 env vars de MLflow y las 3 de autenticación Keycloak. Set mínimo recomendado para dev local:

```bash
# Persistencia — ⚠️ el compose crea la DB con nombre `analytics-ms-db` (POSTGRES_DB), no `analytics_service_db`
DATABASE_URL=postgresql://admin:admin@analytics-ms-db:5432/analytics-ms-db
REDIS_URL=redis://redis:6379/2

# MLflow + MinIO (artifact store)
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
MLFLOW_MODEL_URI=models:/bogota-avm@production
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# Auth — Keycloak JWT (ver [[adr-auth-keycloak-jwt]])
KC_JWKS_URL=http://keycloak:8080/realms/<realm>/protocol/openid-connect/certs
KC_ISSUER=http://keycloak:8080/realms/<realm>
OIDC_AUDIENCE=users-ms

# Kafka — consumer listing-created (solo necesario para el worker, no para el web server)
KAFKA_SERVER=broker:29092
KAFKA_GROUP_ID=analytics-listing-consumer
KAFKA_TOPIC=listing-created
KAFKA_PREDICTIONS_TOPIC=price-predicted
KAFKA_DLQ_TOPIC=listing-created-dlq
WORKER_PRINCIPAL=<uuid-del-principal-de-sistema>
```

El realm es `core` (ver `infra/keycloak/realm-dev.json`).

Los nombres de host (`analytics-ms-db`, `mlflow`, `minio`, `redis`) resuelven en la red `dev-net` del compose desde dentro del devcontainer.

## Verificar `/predict` end-to-end

El endpoint está expuesto en `POST /v1/predict`. Requiere un JWT válido — el servicio lo lee de la **cookie `access_token`** (HttpOnly, seteada por el gateway). Para tests manuales con curl/Postman usar el header `Cookie: access_token=<jwt>`.

1. Obtener un JWT de Keycloak (Postman collection pendiente, ver [[adr-auth-keycloak-jwt]]).
2. POST a `http://localhost:8000/v1/predict` con `Cookie: access_token=<jwt>` y body con shape de `PredictionRequest` (rangos en [[analytics-service-prediction]]).
3. Validar que la response tenga `id`, `predicted_price`, `model_version`, `created_at`.
4. Opcionalmente revisar el registro insertado: `psql -h analytics-ms-db -U admin -d analytics-ms-db -c "SELECT * FROM predictions ORDER BY created_at DESC LIMIT 1;"`

Los gaps #1 a #4 están resueltos: desde el 2026-09-07 `minio-init` crea el bucket y la cuenta con scope.

## Known gaps

~~1. **No hay `analytics-ms-db` en `docker-compose.yml`**.~~ ✓ Resuelto — DB y migraciones corriendo (2026-05-25).
~~2. **No hay migraciones Alembic aplicadas**.~~ ✓ `alembic upgrade head` aplicado, tabla `predictions` activa (2026-05-25).
~~3. **El bucket `mlflow-artifacts` no se crea automáticamente en MinIO**.~~ ✓ Resuelto 2026-09-07: el servicio `minio-init` lo crea junto con los otros tres y le adjunta la policy `mlflow` a un usuario propio. `MINIO_DEFAULT_BUCKETS` se eliminó del compose — la imagen `minio/minio` nunca leyó esa variable (es de Bitnami), así que no hacía nada.
~~4. **No hay modelo seed en MLflow**.~~ ✓ `bogota-avm` con alias `production` disponible — `/predict` y worker batch funcionando end-to-end (2026-05-25).
~~5. **El `.env.example` del servicio está incompleto**.~~ ✓ Env vars MLflow, auth y Kafka documentadas arriba (2026-05-25).
~~6. **La FastAPI dependency de auth no existe**.~~ ✓ Implementada en `api/deps/auth.py` (2026-05-20).
~~7. **El route `/predict` no está wireado en `api/main.py`**.~~ ✓ Expuesto vía `predict.router` incluido en `api/main.py` (2026-05-20).

## Postman collection (pendiente)

Una collection pública para obtener token de Keycloak + llamar `/predict` se creará cuando el gap #3 (bucket MinIO) esté cerrado y haya un realm de Keycloak con un usuario de prueba configurado. Los gaps #1, #2 y #4 ya no bloquean.

## Comandos útiles dentro del devcontainer

```bash
# Re-sync deps después de cambios en pyproject.toml
uv sync

# Instalar deps de test (solo la primera vez, o si cambia pyproject.toml)
uv sync --extra dev

# Correr tests unitarios
uv run python -m pytest tests/unit/

# Conectarse a la DB (postgres-client viene preinstalado vía devcontainer feature)
psql -h analytics-ms-db -U admin -d analytics_service_db

# Ver logs de un service del compose desde el devcontainer
docker logs mlflow -f

# Re-aplicar los client secrets de Keycloak (idempotente)
docker compose up keycloak-init

# Reimportar el realm de cero: --import-realm salta si el realm ya existe,
# asi que hay que borrar el volumen primero
docker compose down && docker volume rm side_keycloak-postgres-data
```

## Claims

- `docker-compose.yml` define 14 services: `develop`, `users-ms-db`, `catalog-ms-db`, `properties-ms-db`, `analytics-ms-db`, `keycloak-db`, `keycloak`, `redis`, `redisinsight`, `minio`, `mlflow`, `kafka-broker`, `topic-init`, `router` ([docker-compose.yml](docker-compose.yml)).
- `analytics-service` (la app) NO está incluida como service en el compose — solo su DB (`analytics-ms-db`) lo está.
- El `develop` service monta el repo root en `/workspace` ([docker-compose.yml:7-8](docker-compose.yml#L7-L8)).
- Keycloak escucha en host port **8180** mapeado al 8080 interno del container ([docker-compose.yml:98-99](docker-compose.yml#L98-L99)).
- MinIO API en host port 9000, consola en 9001 ([docker-compose.yml:130-132](docker-compose.yml#L130-L132)).
- MLflow en host port 5000 con SQLite como backend store en `/mlflow/mlflow.db` ([docker-compose.yml:156](docker-compose.yml#L156)).
- MLflow `--default-artifact-root` apunta a `s3://mlflow-artifacts/`, creado por el servicio `minio-init` desde el 2026-09-07 ([docker-compose.yml](docker-compose.yml)).
- El `postCreateCommand` del devcontainer ejecuta `setup-analytics-kernel.sh`, que registra un Jupyter kernel llamado `analytics` ([devcontainer.json:34](.devcontainer/devcontainer.json#L34), [setup-analytics-kernel.sh](data/ml/AVM/scripts/setup-analytics-kernel.sh)).
- El Dockerfile de analytics-service usa `python:3.10-slim` + uv + `ENV PYTHONPATH=/app/src` + uvicorn sobre `app.main:app` puerto 8000 ([Dockerfile](backend/analytics-service/Dockerfile)).
- `PYTHONPATH=src` es obligatorio para correr el web server o el worker localmente — sin esto `import app` falla con `ModuleNotFoundError`.
- `backend/analytics-service/.env.example` no incluye las env vars de MLflow ni las de auth Keycloak al 2026-05-20 ([.env.example](backend/analytics-service/.env.example)).
- `api/deps/` tiene tres archivos: `auth.py` (JWT cookie → `get_current_principal`), `db.py` (session), `prediction.py` (model + UoW + UC); `__init__.py` vacío.
- `UnauthorizedError` y `ForbiddenError` viven en `core/exceptions/auth.py`, no en `api/deps/auth.py` ([core/exceptions/auth.py](backend/analytics-service/src/app/core/exceptions/auth.py)).
- El endpoint `POST /v1/predict` está activo desde 2026-05-20 — wired en `api/routes/predict.py` e incluido en `api/main.py`.
- El devcontainer base es Ubuntu 22.04 + Node 20 + uv 0.5.21 + pnpm ([.devcontainer/Dockerfile](.devcontainer/Dockerfile)).
