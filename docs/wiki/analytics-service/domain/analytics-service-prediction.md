---
title: Dominio prediction (analytics-service)
status: stable
last-verified: 2026-07-13
owners: [analytics-service]
related:
  - "[[analytics-service]]"
  - "[[analytics-service-architecture]]"
  - "[[avm-training]]"
  - "[[analytics-service-mlflow]]"
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md, ../../../sources/analytics-service/2026-05-20-prediction-wiring-and-batch-uc.md, ../../../sources/analytics-service/2026-05-26-predict-endpoint-form-design.md]
---

## TL;DR

Dominio que sirve predicciones de precio de propiedades vía el modelo AVM cargado al startup desde MLflow. Dos UCs: `OnlinePrediction` (HTTP `/predict`) y `BatchPrediction` (Kafka `listing-created`). Ambos persisten cada predicción para auditoría + futuro feedback al modelo.

## Public surface

Dos schemas Pydantic (`StrictBase`) en [services/prediction/schemas/prediction.py](backend/analytics-service/src/app/services/prediction/schemas/prediction.py).

### `PredictionRequest`

| Campo | Tipo | Validación |
|---|---|---|
| `area_m2` | float | (0, 2000] |
| `bedrooms` | int | [0, 20] |
| `bathrooms` | float | [0, 20] |
| `parking_spots` | int | [0, 20] |
| `stratum` | int | [1, 6] |
| `property_type` | enum | `apartment` \| `house` |
| `year_built` | int? | [1900, 2100] |
| `lat` | float | [-90, 90] |
| `lon` | float | [-180, 180] |
| `barrio_ideca` | str | `min_length=1` (no se valida contra catálogo) |
| `property_id` | UUID? | opcional, identificador del listing si se asocia a uno existente |

Notas:
- `barrio_ideca` viene ya resuelto antes de llegar a este servicio: desde `properties-service` en el flujo batch, o desde el chain frontend (Mapbox → `GET /v1/geo-resolution/by-coordinates` en catalog-ms) en el flujo online. Analytics no hace geocoding — ver [[glossary#barrio-ideca]].
- `property_id` opcional → permite predicciones "anónimas" (usuario explorando antes de publicar).
- Validaciones inspiradas en el rango sano de propiedades de Bogotá; estrato 1-6 es la nomenclatura oficial.

### `PredictionResponse`

| Campo | Tipo |
|---|---|
| `id` | UUID — identificador del registro de la predicción |
| `predicted_price` | float — pesos COP (no log) |
| `model_version` | str — version del MLflow registry |
| `created_at` | datetime |

## Domain model

### Tabla `predictions` ([models/prediction.py:46](backend/analytics-service/src/app/models/prediction.py#L46))

Entidad SQLModel `Prediction`:

- **Input features** (copia de `PredictionRequest`): `area_m2`, `bedrooms`, `bathrooms`, `parking_spots`, `stratum`, `property_type`, `year_built`, `lat`, `lon`, `barrio_ideca`.
- **Output**: `predicted_price` (float, COP).
- **Metadata**: `model_version` (string del registry), `source` (`online` | `batch`), `property_id` (UUID opcional).
- **Feedback**: `feedback` (enum 5 niveles, opcional), `feedback_comment` (str opcional) — alimentados via endpoint futuro de encuesta de satisfacción.
- **Auditoría** (vía `AuditMixin`): `created_at`, `updated_at`, `created_by`, `updated_by`.

Índices: `ix_predictions_model_version`, `ix_predictions_created_at`.

### Enums

| Enum | Valores |
|---|---|
| `PropertyType` | `apartment`, `house` |
| `SourceType` | `online`, `batch` |
| `PredictionFeedback` | `muy_mal`, `mal`, `regular`, `bien`, `muy_bien` |

## Use case: `OnlinePrediction`

Único UC implementado al 2026-05-19. Archivo: [online.py](backend/analytics-service/src/app/services/prediction/use_cases/online.py).

### Dependencias inyectadas
- `uow: PredictionUnitOfWork` — persistencia
- `model: ModelGateway` — inferencia (port)

### Flujo de `execute(principal, req)`
1. `run_in_threadpool(model.online_predict)` → `(predicted_price, model_version)`.
2. `build_prediction_record(source=online)` → `Prediction` (helper compartido con batch).
3. `run_in_threadpool(uow.prediction.add)` — `flush()` es bloqueante, va en threadpool.
4. `await uow.commit()`. Si falla → `rollback()` + `PredictionPersistenceError`.
5. Devuelve `PredictionResponse`.

## Use case: `BatchPrediction`

Archivo: [batch.py](backend/analytics-service/src/app/services/prediction/use_cases/batch.py). Consumido por el worker Kafka del topic `listing-created`.

### Firma
- **Entrada**: `messages: list[tuple[uuid.UUID, PredictionRequest]]` — ID de correlación + objeto armado por el consumer.
- **Salida**: `BatchPredictionResult(predictions: list[tuple[uuid.UUID, float]], failed: list[tuple[uuid.UUID, PredictionRequest]])`.

`principal` = `SYSTEM_PRINCIPAL_ID` (UUID fijo de settings), no un usuario real.

### Flujo de `execute(principal, messages)`
1. `run_in_threadpool(model.batch_predict)` → `(prices, model_version)`. Si falla, propaga — el consumer re-encola el batch entero.
2. `build_prediction_record(source=batch)` × N.
3. **Happy path**: `run_in_threadpool(uow.prediction.batch_add)` con `ON CONFLICT DO NOTHING` + `commit()`.
   - `ON CONFLICT DO NOTHING` protege contra re-entrega at-least-once de Kafka.
4. **Fallback** si bulk falla: `begin_nested()` por fila → `rollback_to_savepoint()` en las que fallan → un solo `commit()` al final.
5. Devuelve `BatchPredictionResult` — el consumer publica `predictions` al topic `price-predicted` y re-encola `failed` a `listing-created`.

## Ports

### `ModelGateway` ([model_gateway.py](backend/analytics-service/src/app/services/prediction/ports/model_gateway.py))
```python
class ModelGateway(Protocol):
    def online_predict(self, *, record: PredictionRequest) -> tuple[float, str]: ...
    def batch_predict(self, *, records: list[PredictionRequest]) -> tuple[list[float], str]: ...
```
- `online_predict` y `batch_predict` implementados en `AVMModelAdapter`.

### `PredictionRepository` ([prediction_repository.py](backend/analytics-service/src/app/services/prediction/ports/prediction_repository.py))
```python
class PredictionRepository(Protocol):
    def add(self, *, record: Prediction) -> None: ...
    def batch_add(self, *, req: list[Prediction]) -> None: ...
```

### `PredictionUnitOfWork` ([unit_of_work.py](backend/analytics-service/src/app/services/prediction/ports/unit_of_work.py))
```python
class PredictionUnitOfWork(Protocol):
    prediction: PredictionRepository
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def refresh(self, instance: object) -> None: ...
    async def begin_nested(self) -> None: ...
    async def rollback_to_savepoint(self) -> None: ...
```

## Adapters

### `AVMModelAdapter` ([avm_model_adapter.py](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py))

Implementa `ModelGateway`. Wrappea `ModelClient` (integración MLflow). Hardcodea:
- `model_name = "bogota-avm"`
- `alias = "production"`

Para cada `online_predict`:
1. `version = client.get_version(model_name, alias)` — consulta el registry.
2. Serializa el request con `record.model_dump(mode='json', exclude={'property_id'})` — `property_id` no es feature del modelo.
3. `price = client.online_predict(record=...)` → float.
4. Devuelve `(price, version)`.

### `SqlPredictionRepository`
- `add`: `session.add(record)` + `session.flush()` — sync, llamado vía `run_in_threadpool`.
- `batch_add`: `insert(Prediction).values([...]).on_conflict_do_nothing()` + `session.execute()` directo — sin `flush()` posterior.

### `build_prediction_record` ([helpers/record_builder.py](backend/analytics-service/src/app/services/prediction/helpers/record_builder.py))
Helper compartido entre `OnlinePrediction` y `BatchPrediction`. Acepta `source: SourceType` para distinguir origen.

## Errores

**`PredictionPersistenceError`** ([core/exceptions/prediction.py](backend/analytics-service/src/app/core/exceptions/prediction.py)): se lanza cuando falla la persistencia tras una predicción exitosa. Extiende `BaseError` con:
- `code = "PREDICTION_PERSISTENCE_ERROR"`
- `http_status = 500`
- `cause` original adjuntada (chain)

## Boundaries — lo que prediction **NO** hace

- **No autentica** — el `principal` llega ya resuelto al UC vía dependency en `api/deps/`.
- **No carga el modelo** — `ModelClient.__init__` lo hace una sola vez al startup del proceso.
- **No promueve modelos** — el alias `production` lo setea el data team. Ver `[[adr-model-promotion-external-to-service]]`.
- **No entrena** — ver [[avm-training]].

## Open items

- Agregar campo `address: Optional[str]` a `PredictionRequest` + columna correspondiente en nueva migración Alembic. Acordado 2026-05-26 para habilitar historial de avalúos — excluir del `model_dump` enviado a MLflow.
- `principal` en batch llega como `str | None` desde `os.getenv('WORKER_PRINCIPAL')` — no castea a `uuid.UUID` ni viene de `settings`. Pendiente normalizar.
- Endpoint de feedback de satisfacción que llene `feedback` + `feedback_comment` por `prediction.id`.

## Claims

- El UC `OnlinePrediction` envuelve la inferencia en `run_in_threadpool` porque MLflow es bloqueante ([online.py:45](backend/analytics-service/src/app/services/prediction/use_cases/online.py#L45)).
- `AVMModelAdapter` hardcodea `model_name="bogota-avm"` y `alias="production"` ([avm_model_adapter.py:10](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L10)).
- `property_id` se excluye del payload enviado a MLflow ([avm_model_adapter.py:11](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L11)).
- `PredictionPersistenceError` mapea a HTTP 500 con code `PREDICTION_PERSISTENCE_ERROR` ([core/exceptions/prediction.py:13](backend/analytics-service/src/app/core/exceptions/prediction.py#L13)).
- `AVMModelAdapter.batch_predict` está implementado: obtiene `version`, llama `client.batch_predict(records=[...])` y retorna `tuple[list[float], str]` ([avm_model_adapter.py:14-17](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L14-L17)).
- El enum `SourceType.batch` se usa en `BatchPrediction.execute` vía `build_prediction_record(source=SourceType.batch)` desde 2026-05-20.
- La tabla `predictions` tiene índices en `model_version` y `created_at` ([models/prediction.py:50-52](backend/analytics-service/src/app/models/prediction.py#L50-L52)).
- `PredictionRequest.barrio_ideca` solo valida `min_length=1`; no se chequea contra ningún catálogo en este servicio ([schemas/prediction.py:21](backend/analytics-service/src/app/services/prediction/schemas/prediction.py#L21)).
- La migración Alembic de la tabla `predictions` existe: `976082b7f322_first_migration_including_predictions_.py` ([migrations/versions/](backend/analytics-service/src/app/migrations/versions/)).
- El endpoint `POST /v1/predict` está completamente wired al 2026-05-26: router, DI (`deps/prediction.py`), `OnlinePrediction` UC y `AVMModelAdapter` ([api/main.py](backend/analytics-service/src/app/api/main.py), [deps/prediction.py](backend/analytics-service/src/app/api/deps/prediction.py)).
