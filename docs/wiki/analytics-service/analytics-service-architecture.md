---
title: Arquitectura interna de analytics-service
status: draft
last-verified: 2026-06-16
owners: [analytics-service]
related:
  - "[[architecture]]"
  - "[[analytics-service]]"
  - "[[analytics-service-prediction]]"
  - "[[analytics-service-mlflow]]"
  - "[[analytics-service-kafka-consumer]]"
sources:
  - ../../sources/analytics-service/2026-05-19-foundational-qa.md
  - ../../sources/analytics-service/2026-05-20-prediction-wiring-and-batch-uc.md
  - ../../sources/analytics-service/2026-05-20-kafka-consumer-design.md
  - ../../sources/analytics-service/2026-05-23-worker-runner-kafka-idempotency.md
---

## TL;DR

Hex pattern estándar del backend con dos dominios (`prediction` activo, `market` vacío). Tres capas: `api/` (HTTP), `services/<domain>/` (use cases + ports + adapters + schemas), `integrations/` (clientes a infra externa). Persistencia vía SQLModel a Postgres. Modelo ML cargado **al startup** vía el adapter de MLflow.

## Layout

```
src/app/
├── api/
│   ├── deps/
│   │   ├── auth.py           # get_current_principal, PyJWKClient
│   │   ├── db.py             # get_session (wrapper sobre app.db)
│   │   └── prediction.py     # lru_cache model/adapter, get_uow, get_online_prediction_uc
│   ├── handlers/
│   │   └── exception_handlers.py
│   ├── middleware/
│   │   └── correlation_id.py
│   └── routes/
│       ├── health.py
│       └── predict.py        # POST /predict → OnlinePrediction
├── core/
│   ├── config/settings.py    # DATABASE_ANALYTICS_URL, REDIS_URL, KC_JWKS_URL, KC_ISSUER, OIDC_AUDIENCE
│   ├── exceptions/
│   │   ├── base.py
│   │   ├── auth.py           # UnauthorizedError, ForbiddenError
│   │   └── prediction.py     # PredictionPersistenceError
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
| UC online | [`services/prediction/use_cases/online.py`](backend/analytics-service/src/app/services/prediction/use_cases/online.py) |
| UC batch | [`services/prediction/use_cases/batch.py`](backend/analytics-service/src/app/services/prediction/use_cases/batch.py) |
| Helper | `services/prediction/helpers/record_builder.py` — `build_prediction_record` compartido |
| Port: model gateway | `services/prediction/ports/model_gateway.py` |
| Port: prediction repo | `services/prediction/ports/prediction_repository.py` |
| Port: UoW | `services/prediction/ports/unit_of_work.py` |
| Adapter: model | `services/prediction/adapters/avm_model_adapter.py` |
| Adapter: SQL repo | `services/prediction/adapters/sql_prediction_repository.py` |
| Adapter: SQL UoW | `services/prediction/adapters/sql_prediction_unit_of_work.py` |
| Schemas | `services/prediction/schemas/prediction.py` |
| Modelo de BD | `models/prediction.py` (tabla `predictions`) |
| Error de dominio | `core/exceptions/prediction.py` |

### Flujo de `OnlinePrediction.execute`
1. Recibe `PredictionRequest` y `principal: uuid.UUID` (resuelto del JWT por `get_current_principal`).
2. `run_in_threadpool(model.online_predict)` → `(predicted_price, model_version)`. Bloqueante — MLflow es sync.
3. `build_prediction_record(source=online)` → entidad `Prediction`.
4. `run_in_threadpool(uow.prediction.add)` + `await uow.commit()`. `flush()` dentro de `add` es bloqueante, también va en threadpool.
5. Si persiste falla → `rollback()` + `PredictionPersistenceError`.
6. Devuelve `PredictionResponse`.

### Flujo de `BatchPrediction.execute`
Entrada: `messages: list[tuple[uuid.UUID, PredictionRequest]]` — el consumer arma el objeto, pasa con un ID de correlación.

1. `run_in_threadpool(model.batch_predict)` → `(prices, model_version)`. DataFrame multi-fila.
2. `build_prediction_record(source=batch)` × N → `db_records`.
3. **Happy path**: `run_in_threadpool(uow.prediction.batch_add)` con `ON CONFLICT DO NOTHING` + `commit()`.
4. **Fallback** si falla bulk: `begin_nested()` por fila → `rollback_to_savepoint()` en las que fallan → un solo `commit()` al final.
5. Devuelve `BatchPredictionResult(predictions=[(id, price)], failed=[(id, req)])`.

`principal` en batch = `SYSTEM_PRINCIPAL_ID` (UUID fijo de settings) — representa a `properties-service` como actor, no a un usuario. Protege la auditoría en `created_by`.

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
- `get_version(model_name, alias)` → version string del alias en el registry.
- `online_predict(record)` → DataFrame de 1 fila → `pyfunc.predict().iloc[0]`.
- `batch_predict(records)` → DataFrame multi-fila → `pyfunc.predict().tolist()`.

El adapter `AVMModelAdapter` consume `ModelClient` y traduce entre el schema del dominio (`PredictionRequest`) y el formato dict que MLflow espera. **Hardcodea hoy** `model_name="bogota-avm"` y `alias="production"`.

Ver [[analytics-service-mlflow]] para el detalle.

### Redis, MinIO directo
Scaffoldeados en `integrations/cache/redis/` y `integrations/storage/minio/`. **No usados en código de runtime hoy**. Reservados para casos futuros (rate limit, reverse ETL del heatmap).

## Persistencia

Postgres vía SQLModel. Una sola tabla activa hoy:

- **`predictions`** ([models/prediction.py:46](backend/analytics-service/src/app/models/prediction.py#L46)): guarda cada predicción con sus inputs, output, `model_version`, `source` (online|batch), `feedback` (5 niveles, opcional), `feedback_comment`. Audit fields heredados de `AuditMixin` (`created_at`, `updated_at`, `created_by`, `updated_by`). Índices en `model_version` y `created_at`.

> ✅ **Resuelto (2026-05-25)**: al 2026-05-19 Alembic estaba configurado en `pyproject.toml` pero sin migraciones aplicadas — la tabla no se materializaba via Alembic. Ya no: la migración `976082b7f322_first_migration_including_predictions_.py` existe y está aplicada (`alembic upgrade head`), tabla `predictions` activa ([migrations/versions/](backend/analytics-service/src/app/migrations/versions/)).

## Auth en el servicio

JWT del usuario llega vía la cookie `access_token` (mismo patrón que catalog/properties/users). Una FastAPI dependency en `api/deps/` resuelve el token contra Keycloak y entrega un `principal: uuid.UUID` al UC. Los UCs **nunca ven el token** ni hablan con Keycloak — operan sobre el UUID resuelto.

Para el flujo server-to-server (Kafka), el `principal` es `SYSTEM_PRINCIPAL_ID` (UUID fijo en settings), no el usuario real. Ver `[[adr-auth-keycloak-jwt]]`.

`api/deps/auth.py` implementa `get_current_principal` — lee cookie `access_token`, valida JWT contra Keycloak vía `PyJWKClient`. `UnauthorizedError` y `ForbiddenError` viven en `core/exceptions/auth.py` (no en el dep).

## Errores y exception handling

Jerarquía en `core/exceptions/`:
- `base.py` — base class
- `prediction.py` — errores del dominio prediction (ej: `PredictionPersistenceError`)

`api/handlers/exception_handlers.py` registra los handlers en el FastAPI app via `register_exception_handlers(app)` en el factory de `main.py`. Cada error de dominio se mapea a un response HTTP estándar.

## Middleware

Uno hoy: **correlation_id** ([api/middleware/correlation_id.py](backend/analytics-service/src/app/api/middleware/correlation_id.py)). Genera un UUID por request y lo propaga en logs + response header para trazabilidad. Aplicado vía `add_correlation_id(app)` en `main.py`.

## Workers

Dos archivos activos en `src/app/workers/listing_created/`:

- **`consumer.py`** — `ListingConsumer`: poll Kafka, validación con `WorkerMessage`, call al UC, tres produces (predictions / retry / DLQ), commit manual de offsets.
- **`runner.py`** — `ListingWorkerRunner`: orquesta el DI manual y el loop `while True / sleep(900)`.

El DI del worker es manual (no hay FastAPI `Depends`). `ModelClient` y `AVMModelAdapter` se crean en `__init__` como singletons — el modelo se carga una sola vez al startup. La `Session(engine)` se abre dentro de `run()` para que viva durante todo el ciclo del proceso.

Decisiones de diseño:
- **confluent-kafka** (no aiokafka) — librdkafka bajo el capó.
- **Proceso separado long-running** — mantiene el modelo en memoria entre ciclos; ciclo de vida independiente del web server.
- **`enable.auto.commit: False`** — commit manual al final de cada batch (at-least-once).
- **DLQ** (`KAFKA_DLQ_TOPIC`) para decode failures (base64 JSON con metadata), errores de validación y `attempts > 3`. Fallos de modelo van de vuelta a `KAFKA_TOPIC` vía `BatchPredictionResult.failed` con `attempts + 1`.
- **Sin constraint único en `predictions.property_id`** — múltiples predicciones por listing son válidas como histórico. `on_conflict_do_nothing` en `batch_add` como red de seguridad.

Ver [[analytics-service-kafka-consumer]] para el detalle.

## Claims

- `api/deps/` tiene tres archivos: `auth.py` (JWT), `db.py` (session), `prediction.py` (model + UoW + UC); `__init__.py` vacío.
- En el path HTTP, `ModelClient` y `AVMModelAdapter` se instancian con `@lru_cache(maxsize=1)` en `api/deps/prediction.py` — singleton por proceso uvicorn ([deps/prediction.py](backend/analytics-service/src/app/api/deps/prediction.py)).
- En el worker, `ModelClient` y `AVMModelAdapter` se instancian directamente en `ListingWorkerRunner.__init__` — singleton por proceso worker, independiente del anterior ([runner.py](backend/analytics-service/src/app/workers/listing_created/runner.py)).
- `run_in_threadpool` se aplica tanto a la inferencia (`online_predict`, `batch_predict`) como al repo (`add`, `batch_add`) — ambas son operaciones bloqueantes ([online.py](backend/analytics-service/src/app/services/prediction/use_cases/online.py), [batch.py](backend/analytics-service/src/app/services/prediction/use_cases/batch.py)).
- `UnauthorizedError` y `ForbiddenError` viven en `core/exceptions/auth.py`, no en el dep ([core/exceptions/auth.py](backend/analytics-service/src/app/core/exceptions/auth.py)).
- El `api_router` incluye `health.router` y `predict.router` ([api/main.py](backend/analytics-service/src/app/api/main.py)).
- `core/config/settings.py` declara `DATABASE_ANALYTICS_URL`, `REDIS_URL`, `KC_JWKS_URL`, `KC_ISSUER`, `OIDC_AUDIENCE`; las env vars de MLflow se leen directamente en `ModelClient.__init__` ([mlflow/model.py:11](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L11)).
- `ModelClient` carga el modelo al instanciarse (`__init__`), no on-demand ([mlflow/model.py:29](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L29)).
- `SqlPredictionUnitOfWork` implementa `begin_nested()` y `rollback_to_savepoint()` — necesarios para el fallback row-by-row del UC batch ([sql_prediction_unit_of_work.py](backend/analytics-service/src/app/services/prediction/adapters/sql_prediction_unit_of_work.py)).
- Migración Alembic aplicada al 2026-05-25 — tabla `predictions` activa en `migrations/versions/` ([migrations/versions/](backend/analytics-service/src/app/migrations/versions/)).
- `workers/listing_created/consumer.py` define `ListingConsumer(uc: BatchPrediction)` — producer se crea internamente, no se inyecta ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- `workers/listing_created/runner.py` define `ListingWorkerRunner` — singletons en `__init__`, sesión en `run()`, loop `while True / asyncio.sleep(900)` ([runner.py](backend/analytics-service/src/app/workers/listing_created/runner.py)).
- `WorkerMessage` en `helpers/types.py` es Pydantic `StrictBase`, no TypedDict — valida el envelope Kafka completo incluyendo `attempts: int = Field(ge=1, strict=True)`.
