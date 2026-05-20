---
title: Runbook — analytics-service local dev
status: draft
last-verified: 2026-05-20
owners: [analytics-service]
related: [[analytics-service]], [[analytics-service-architecture]], [[avm-training]], [[adr-mlflow-minio-stack]]
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
---

## TL;DR

Flujo: abrir el repo en VS Code → "Reopen in Container" → docker-compose levanta toda la infra (Postgres por servicio + Keycloak + Redis + MinIO + MLflow). Después, **a mano**: `cd backend/analytics-service && uv sync && uv run uvicorn app.main:app --reload --port 8000`.

El servicio analytics **no está como service en el compose** — se corre manual dentro del devcontainer. Y hay 7 gaps actuales que bloquean `/predict` end-to-end (ver Known gaps al final).

## Prerequisites

- Docker Desktop (o engine equivalente) corriendo.
- VS Code con la extensión **Dev Containers** (`ms-vscode-remote.remote-containers`).
- Repo clonado.
- Archivo `.env` en el root del repo (se necesita para el users-service hoy; si no está, pedirlo al equipo).

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
| `catalog-ms-db` | postgis/postgis:17 | (interno) | DB de catalog-service | admin / admin |
| `properties-ms-db` | postgis/postgis:17 | (interno) | DB de properties-service | admin / admin |
| `keycloak-db` | postgres:17 | (interno) | DB de Keycloak | keycloak / password |
| `keycloak` | keycloak:26.4.7 | **8180** | IdP — admin UI en http://localhost:8180 | admin / admin |
| `redis` | redis:latest | 6379 | Cache + rate limit | n/a |
| `redisinsight` | redis/redisinsight | 5540 | UI de Redis — http://localhost:5540 | n/a |
| `minio` | minio:RELEASE.2025-09-07 | 9000 (API), **9001** (console) | Artifact store — console en http://localhost:9001 | minioadmin / minioadmin |
| `mlflow` | mlflow:v3.12.0-full | 5000 | Model registry + tracking — UI en http://localhost:5000 | n/a |

**Nota**: NO hay un `analytics-ms-db` en el compose — ver gap #1 abajo.

## Correr analytics-service

Dentro del devcontainer:

```bash
cd /workspace/backend/analytics-service
uv sync
# crear .env del servicio — ver siguiente sección
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:
```bash
curl http://localhost:8000/v1/health
```

## Env vars del servicio

`backend/analytics-service/.env.example` **está incompleto** al 2026-05-20: solo declara `DATABASE_URL` y `REDIS_URL`. Para que `/predict` funcione, el `.env` real necesita además las 5 env vars de MLflow. Set mínimo recomendado para dev local:

```bash
# Persistencia
DATABASE_URL=postgresql://admin:admin@analytics-ms-db:5432/analytics_service_db
REDIS_URL=redis://redis:6379/2

# MLflow + MinIO (artifact store)
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_S3_ENDPOINT_URL=http://minio:9000
MLFLOW_MODEL_URI=models:/bogota-avm@production
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
```

Los nombres de host (`analytics-ms-db`, `mlflow`, `minio`, `redis`) resuelven en la red `dev-net` del compose desde dentro del devcontainer.

## Verificar `/predict` end-to-end

**Pendiente** — el endpoint `/predict` todavía no está expuesto en `api/main.py` al 2026-05-20. Cuando se exponga, el flujo será:

1. Obtener un JWT de Keycloak (Postman collection pendiente, ver [[adr-auth-keycloak-jwt]]).
2. POST a `http://localhost:8000/v1/predict` con `Authorization: Bearer <jwt>` y body con shape de `PredictionRequest` (rangos en [[analytics-service-prediction]]).
3. Validar la response y opcionalmente revisar el registro insertado en `predictions`.

## Known gaps (2026-05-20)

Estos son blockers para llegar a un `/predict` funcionando en local. Surgieron escribiendo este runbook; ningún issue creado todavía.

1. **No hay `analytics-ms-db` en `docker-compose.yml`.** Los otros servicios tienen Postgres dedicado, analytics no. Agregar un block análogo a `properties-ms-db`.
2. **No hay migraciones Alembic aplicadas.** La tabla `predictions` está modelada pero no se ha generado migración. Antes de levantar: `alembic revision --autogenerate -m "create predictions"` + `alembic upgrade head`.
3. **El bucket `mlflow-artifacts` no se crea automáticamente en MinIO.** MLflow está configurado con `--default-artifact-root s3://mlflow-artifacts/`, pero MinIO solo crea `mi-casa-en-minutos` por default. Crear el bucket manualmente desde la console (http://localhost:9001) o ajustar la config del compose.
4. **No hay modelo seed en MLflow.** Para que `/predict` responda, el registry necesita `bogota-avm` con alias `production`. Opciones:
   - Correr `python data/ml/AVM/training/train.py` contra un dataset (CSV en `data/raw/` si existe).
   - Pre-cargar un modelo entrenado (mecanismo pendiente).
5. **El `.env.example` del servicio está incompleto** — faltan las 5 env vars de MLflow (documentadas arriba).
6. **La FastAPI dependency de auth no existe** (`api/deps/__init__.py` vacío). Hoy no se puede testear el flujo auth real — se necesita stub o mock hasta que se implemente.
7. **El route `/predict` no está wireado en `api/main.py`.** Solo `/health` está activo.

## Postman collection (pendiente)

Una collection pública para obtener token de Keycloak + llamar `/predict` se creará cuando el endpoint exista y la dependency de auth esté implementada.

## Comandos útiles dentro del devcontainer

```bash
# Re-sync deps después de cambios en pyproject.toml
uv sync

# Correr tests
uv run pytest

# Conectarse a la DB (postgres-client viene preinstalado vía devcontainer feature)
psql -h analytics-ms-db -U admin -d analytics_service_db

# Ver logs de un service del compose desde el devcontainer
docker logs mlflow -f

# Recargar el realm de Keycloak (si cambia infra/keycloak/realm.template.json)
docker compose restart keycloak
```

## Claims

- `docker-compose.yml` define 10 services: `develop`, `users-ms-db`, `catalog-ms-db`, `properties-ms-db`, `keycloak-db`, `keycloak`, `redis`, `redisinsight`, `minio`, `mlflow` ([docker-compose.yml](docker-compose.yml)).
- `analytics-service` NO está incluido como service en el compose al 2026-05-20.
- El `develop` service monta el repo root en `/workspace` ([docker-compose.yml:7-8](docker-compose.yml#L7-L8)).
- Keycloak escucha en host port **8180** mapeado al 8080 interno del container ([docker-compose.yml:87-88](docker-compose.yml#L87-L88)).
- MinIO API en host port 9000, consola en 9001 ([docker-compose.yml:119-121](docker-compose.yml#L119-L121)).
- MLflow en host port 5000 con SQLite como backend store en `/mlflow/mlflow.db` ([docker-compose.yml:142-147](docker-compose.yml#L142-L147)).
- MLflow `--default-artifact-root` apunta a `s3://mlflow-artifacts/`, bucket que **no** está en `MINIO_DEFAULT_BUCKETS` ([docker-compose.yml:127](docker-compose.yml#L127), [docker-compose.yml:146](docker-compose.yml#L146)).
- El `postCreateCommand` del devcontainer ejecuta `setup-analytics-kernel.sh`, que registra un Jupyter kernel llamado `analytics` ([devcontainer.json:31-33](.devcontainer/devcontainer.json#L31-L33), [setup-analytics-kernel.sh](data/ml/AVM/scripts/setup-analytics-kernel.sh)).
- El Dockerfile de analytics-service usa `python:3.10-slim` + uv + uvicorn sobre `app.main:app` puerto 8000 ([Dockerfile](backend/analytics-service/Dockerfile)).
- `backend/analytics-service/.env.example` no incluye las env vars de MLflow al 2026-05-20 ([.env.example](backend/analytics-service/.env.example)).
- El devcontainer base es Ubuntu 22.04 + Node 20 + uv 0.5.21 + pnpm ([.devcontainer/Dockerfile](.devcontainer/Dockerfile)).
