---
title: Arquitectura interna de analytics-service
status: draft
last-verified: 2026-05-19
owners: [analytics-service]
related: [[architecture]], [[analytics-service]], [[analytics-service-prediction]], [[analytics-service-mlflow]]
sources: [../../sources/analytics-service/2026-05-19-foundational-qa.md]
---

## TL;DR

Hex pattern estándar del backend con dos dominios (`prediction` activo, `market` vacío). Tres capas: `api/` (HTTP), `services/<domain>/` (use cases + ports + adapters + schemas), `integrations/` (clientes a infra externa). Persistencia vía SQLModel a Postgres. Modelo ML cargado **al startup** vía el adapter de MLflow.

## Layout

```
src/app/
├── api/
│   ├── deps/                 # dependencies FastAPI (auth, db, model client, UoW)
│   ├── handlers/
│   │   └── exception_handlers.py
│   ├── middleware/
│   │   └── correlation_id.py
│   └── routes/
│       └── health.py         # único router activo hoy
├── core/
│   ├── config/settings.py    # DATABASE_URL, REDIS_URL
│   ├── exceptions/
│   │   ├── base.py
│   │   └── prediction.py     # PredictionPersistenceError, etc.
│   └── logging/
├── db/                       # session, engine
├── integrations/
│   ├── cache/redis/          # cliente Redis (scaffolded)
│   ├── ml/mlflow/model.py    # ModelClient — wrapper sobre MLflow + MinIO
│   └── storage/minio/        # cliente MinIO directo (scaffolded)
├── models/
│   └── prediction.py         # SQLModel Prediction + enums
├── schemas/                  # DTOs base/principal compartidos
├── services/
│   ├── prediction/           # dominio activo
│   ├── market/               # dominio scaffoldeado, vacío
│   └── shared/               # adapters/ports compartidos entre dominios
├── workers/                  # consumers async (pendiente)
└── main.py                   # FastAPI app factory
```

Reglas del layout (comunes a todos los microservicios, ver [[architecture]]):
- Use cases en `services/<domain>/use_cases/` son los **entry points** del dominio.
- Use cases dependen de **ports** (`services/<domain>/ports/`), nunca de adapters concretos.
- Adapters concretos viven en `services/<domain>/adapters/`.
- Adapters inyectan sus dependencias externas vía constructor; las del UC se resuelven en `api/deps/` con FastAPI.

## Dominio `prediction`

Componentes hoy:

| Pieza | Archivo |
|---|---|
| UC | [`services/prediction/use_cases/online.py`](backend/analytics-service/src/app/services/prediction/use_cases/online.py) |
| Port: model gateway | `services/prediction/ports/model_gateway.py` |
| Port: prediction repo | `services/prediction/ports/prediction_repository.py` |
| Port: UoW | `services/prediction/ports/unit_of_work.py` |
| Adapter: model | `services/prediction/adapters/avm_model_adapter.py` |
| Adapter: SQL repo | `services/prediction/adapters/sql_prediction_repository.py` |
| Schemas (request/response) | `services/prediction/schemas/prediction.py` |
| Modelo de BD | `models/prediction.py` (tabla `predictions`) |
| Error de dominio | `core/exceptions/prediction.py` |

### Flujo de `OnlinePrediction.execute`
1. Recibe `PredictionRequest` validado por Pydantic (`StrictBase`) y un `principal: uuid.UUID` (resuelto del JWT por una dependency).
2. Llama `ModelGateway.online_predict(record=req)` que devuelve `(predicted_price, model_version)`. La llamada está envuelta en `run_in_threadpool` porque la inferencia de MLflow es **sincrónica/bloqueante**.
3. Construye una entidad `Prediction` con inputs + output + `model_version` + `source=online`.
4. Persiste vía `UnitOfWork.prediction.add(...)` + `commit()`. Si falla → `rollback()` + `PredictionPersistenceError`.
5. Devuelve `PredictionResponse(id, predicted_price, model_version, created_at)`.

Ver [[analytics-service-prediction]] para detalle del dominio.

## Dominio `market`

Scaffoldeado (`use_cases/`, `adapters/`, `ports/`, `services/`, `schemas/`, `helpers/`) pero **vacío al 2026-05-19**. Albergará los jobs batch de heatmap, neighborhood reports y anomaly detection.

## Dominio `shared`

Componentes que se usen desde varios dominios (`services/shared/{adapters, db, helpers, policies, ports, schemas}`). Vacío hoy salvo placeholders.

## Capa de integración

### MLflow (`integrations/ml/mlflow/model.py`)
`ModelClient` wrappea las llamadas al server MLflow y **carga el modelo al startup** (en `__init__`). Requiere 5 env vars:

| Env var | Para qué |
|---|---|
| `MLFLOW_TRACKING_URI` | URL del tracking server |
| `MLFLOW_S3_ENDPOINT_URL` | URL de MinIO (S3 endpoint) |
| `MLFLOW_MODEL_URI` | URI del modelo a cargar (ej: `models:/bogota-avm@production`) |
| `AWS_ACCESS_KEY_ID` | Credencial S3/MinIO |
| `AWS_SECRET_ACCESS_KEY` | Credencial S3/MinIO |

Falla en init si falta cualquiera.

Métodos:
- `get_version(model_name, alias)` → consulta el registry y devuelve el version string que apunta el alias.
- `online_predict(record)` → arma un DataFrame de 1 fila y llama `pyfunc.predict()`.

El adapter `AVMModelAdapter` consume `ModelClient` y traduce entre el schema del dominio (`PredictionRequest`) y el formato dict que MLflow espera. **Hardcodea hoy** `model_name="bogota-avm"` y `alias="production"`.

Ver [[analytics-service-mlflow]] para el detalle.

### Redis, MinIO directo
Scaffoldeados en `integrations/cache/redis/` y `integrations/storage/minio/`. **No usados en código de runtime hoy**. Reservados para casos futuros (rate limit, reverse ETL del heatmap).

## Persistencia

Postgres vía SQLModel. Una sola tabla activa hoy:

- **`predictions`** ([models/prediction.py:46](backend/analytics-service/src/app/models/prediction.py#L46)): guarda cada predicción con sus inputs, output, `model_version`, `source` (online|batch), `feedback` (5 niveles, opcional), `feedback_comment`. Audit fields heredados de `AuditMixin` (`created_at`, `updated_at`, `created_by`, `updated_by`). Índices en `model_version` y `created_at`.

Alembic está configurado en `pyproject.toml` pero **no hay migraciones aplicadas al 2026-05-19** — la tabla todavía no se materializa via Alembic. Pendiente.

## Auth en el servicio

JWT del usuario llega vía `Authorization: Bearer <token>`. Una FastAPI dependency en `api/deps/` resuelve el token contra Keycloak y entrega un `principal: uuid.UUID` al UC. Los UCs **nunca ven el token** ni hablan con Keycloak — operan sobre el UUID resuelto.

Para el caso server-to-server (consumer async futuro), el `principal` será un **system ID fijo** del servicio que emite el mensaje. Ver `[[adr-auth-keycloak-jwt]]`.

El dependency concreto **no existe en código todavía** — al 2026-05-19 `api/deps/__init__.py` está vacío.

## Errores y exception handling

Jerarquía en `core/exceptions/`:
- `base.py` — base class
- `prediction.py` — errores del dominio prediction (ej: `PredictionPersistenceError`)

`api/handlers/exception_handlers.py` registra los handlers en el FastAPI app via `register_exception_handlers(app)` en el factory de `main.py`. Cada error de dominio se mapea a un response HTTP estándar.

## Middleware

Uno hoy: **correlation_id** ([api/middleware/correlation_id.py](backend/analytics-service/src/app/api/middleware/correlation_id.py)). Genera un UUID por request y lo propaga en logs + response header para trazabilidad. Aplicado vía `add_correlation_id(app)` en `main.py`.

## Workers (anticipado)

`src/app/workers/` existe como scaffold para los consumers async (caso `properties-service` ↔ `analytics-service` descrito en [[architecture]]). **Sin código aún**. Patrón esperado: cada worker en un módulo dentro de `workers/`, reusando los UCs del dominio (no duplicar la lógica de predicción).

## Claims

- El layout sigue el hex pattern del backend: ports en `services/<domain>/ports/`, adapters en `services/<domain>/adapters/`, UCs en `services/<domain>/use_cases/`.
- El UC `OnlinePrediction` invoca `ModelGateway.online_predict()` envuelto en `run_in_threadpool` porque la llamada a MLflow es bloqueante ([online.py:45](backend/analytics-service/src/app/services/prediction/use_cases/online.py#L45)).
- El adapter `AVMModelAdapter` hardcodea `model_name="bogota-avm"` y `alias="production"` ([avm_model_adapter.py:10](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L10)).
- `ModelClient` carga el modelo al instanciarse (`__init__`), no on-demand ([mlflow/model.py:29](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L29)).
- La factory del FastAPI app está en [main.py:9](backend/analytics-service/src/app/main.py#L9) y registra: logging, correlation_id middleware, exception handlers, y el `api_router` bajo prefix `/v1`.
- El `api_router` solo incluye `health.router` al 2026-05-19 — `predict` no está expuesto ([api/main.py:6](backend/analytics-service/src/app/api/main.py#L6)).
- `api/deps/__init__.py` está vacío al 2026-05-19 — la dependency de auth aún no existe en código.
- `core/config/settings.py` solo declara `DATABASE_URL` y `REDIS_URL`; las env vars de MLflow se leen directamente en `ModelClient.__init__`, no via Settings ([settings.py:6](backend/analytics-service/src/app/core/config/settings.py#L6), [mlflow/model.py:11](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L11)).
- No hay migraciones de Alembic aplicadas al 2026-05-19 (sin archivos en `migrations/versions/`).
- Existe un script provisional [scripts/smoke_online_predict.py](backend/analytics-service/scripts/smoke_online_predict.py) que NO se documenta — provisional según directiva del autor.
