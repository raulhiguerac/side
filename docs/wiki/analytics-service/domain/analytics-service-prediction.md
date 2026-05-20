---
title: Dominio prediction (analytics-service)
status: draft
last-verified: 2026-05-19
owners: [analytics-service]
related: [[analytics-service]], [[analytics-service-architecture]], [[avm-training]], [[analytics-service-mlflow]]
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
---

## TL;DR

Dominio que sirve predicciones de precio de propiedades vía el modelo AVM cargado al startup desde MLflow. El UC sincrónico `OnlinePrediction` es el único caso de uso implementado hoy. Persiste cada predicción para auditoría + futuro feedback al modelo.

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
- `barrio_ideca` viene ya resuelto en el request por `properties-service` — ver [[glossary#barrio-ideca]]. Analytics no hace geocoding.
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
| `SourceType` | `online`, `batch` (batch reservado para el consumer async, sin UC todavía) |
| `PredictionFeedback` | `muy_mal`, `mal`, `regular`, `bien`, `muy_bien` |

## Use case: `OnlinePrediction`

Único UC implementado al 2026-05-19. Archivo: [online.py](backend/analytics-service/src/app/services/prediction/use_cases/online.py).

### Dependencias inyectadas
- `uow: PredictionUnitOfWork` — persistencia
- `model: ModelGateway` — inferencia (port)

### Flujo de `execute(principal, req)`
1. Llama `self.model.online_predict(record=req)` envuelto en `run_in_threadpool` (MLflow es bloqueante).
2. Recibe `(predicted_price: float, model_version: str)`.
3. Construye `Prediction` con inputs + output + `source=online` + `created_by=principal`.
4. `self.uow.prediction.add(record=db_record)` + `await self.uow.commit()`.
5. Si falla cualquier paso de persistencia: `await self.uow.rollback()` + `raise PredictionPersistenceError(cause=exc)`.
6. Devuelve `PredictionResponse(id, predicted_price, model_version, created_at)`.

## Ports

### `ModelGateway` ([model_gateway.py](backend/analytics-service/src/app/services/prediction/ports/model_gateway.py))
```python
class ModelGateway(Protocol):
    def online_predict(self, *, record: PredictionRequest) -> tuple[float, str]: ...
    def batch_predict(self, *, records: list[PredictionRequest]) -> tuple[list[float], str]: ...
```
- `online_predict` está implementado en `AVMModelAdapter`.
- `batch_predict` está declarado pero **no implementado** en el adapter (comentado). Será necesario al implementar el consumer async.

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
Implementa `PredictionRepository` contra Postgres vía SQLModel. Detalles en `[[analytics-service-architecture]]` y en el archivo `sql_prediction_repository.py`.

## Errores

**`PredictionPersistenceError`** ([core/exceptions/prediction.py](backend/analytics-service/src/app/core/exceptions/prediction.py)): se lanza cuando falla la persistencia tras una predicción exitosa. Extiende `BaseError` con:
- `code = "PREDICTION_PERSISTENCE_ERROR"`
- `http_status = 500`
- `cause` original adjuntada (chain)

## Boundaries — lo que prediction **NO** hace

- **No expone HTTP routes** — el wiring de `/predict` está pendiente en `api/routes/`.
- **No autentica** — el `principal` llega ya resuelto al UC vía dependency en `api/deps/`.
- **No carga el modelo** — `ModelClient.__init__` lo hace una sola vez al startup del proceso.
- **No promueve modelos** — el alias `production` lo setea el data team. Ver `[[adr-model-promotion-external-to-service]]`.
- **No entrena** — ver [[avm-training]].
- **No procesa lotes hoy** — `batch_predict` declarado pero no implementado.

## Open items

- Exponer route `/predict` en `api/main.py` (dependency de auth + handler de excepción).
- Endpoint de feedback de satisfacción que llene `feedback` + `feedback_comment` por `prediction.id`.
- Implementar `batch_predict` en el adapter (descomentar + ajustar) cuando se cree el consumer del topic `listing-created`.
- Migración Alembic de la tabla `predictions`.

## Claims

- El UC `OnlinePrediction` envuelve la inferencia en `run_in_threadpool` porque MLflow es bloqueante ([online.py:45](backend/analytics-service/src/app/services/prediction/use_cases/online.py#L45)).
- `AVMModelAdapter` hardcodea `model_name="bogota-avm"` y `alias="production"` ([avm_model_adapter.py:10](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L10)).
- `property_id` se excluye del payload enviado a MLflow ([avm_model_adapter.py:11](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L11)).
- `PredictionPersistenceError` mapea a HTTP 500 con code `PREDICTION_PERSISTENCE_ERROR` ([core/exceptions/prediction.py:13](backend/analytics-service/src/app/core/exceptions/prediction.py#L13)).
- `ModelGateway.batch_predict` está declarado en el port pero comentado en el adapter — no implementado ([avm_model_adapter.py:14-17](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L14-L17)).
- El enum `SourceType` tiene valor `batch` reservado pero no se usa en runtime al 2026-05-19.
- La tabla `predictions` tiene índices en `model_version` y `created_at` ([models/prediction.py:50-52](backend/analytics-service/src/app/models/prediction.py#L50-L52)).
- `PredictionRequest.barrio_ideca` solo valida `min_length=1`; no se chequea contra ningún catálogo en este servicio ([schemas/prediction.py:21](backend/analytics-service/src/app/services/prediction/schemas/prediction.py#L21)).
