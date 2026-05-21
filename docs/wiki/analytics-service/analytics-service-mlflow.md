---
title: MLflow en analytics-service
status: draft
last-verified: 2026-05-20
owners: [analytics-service]
related: [[analytics-service]], [[analytics-service-architecture]], [[avm-training]], [[adr-mlflow-minio-stack]]
sources: [../../sources/analytics-service/2026-05-19-foundational-qa.md, ../../sources/analytics-service/2026-05-20-prediction-wiring-and-batch-uc.md]
---

## TL;DR

`ModelClient` wrappea el SDK de MLflow y carga el modelo al startup. MinIO actúa como artifact store S3-compatible. El modelo en memoria no se reemplaza hasta un restart — la versión activa la controla el alias `production` en el registry.

## `ModelClient` ([integrations/ml/mlflow/model.py](backend/analytics-service/src/app/integrations/ml/mlflow/model.py))

Instanciado con `@lru_cache(maxsize=1)` en `api/deps/prediction.py` — singleton por proceso.

### Env vars requeridas en startup

| Env var | Para qué |
|---|---|
| `MLFLOW_TRACKING_URI` | URL del tracking server (ej: `http://mlflow:5000`) |
| `MLFLOW_S3_ENDPOINT_URL` | URL de MinIO como S3 endpoint (ej: `http://minio:9000`) |
| `MLFLOW_MODEL_URI` | URI del modelo (ej: `models:/bogota-avm@production`) |
| `AWS_ACCESS_KEY_ID` | Credencial MinIO |
| `AWS_SECRET_ACCESS_KEY` | Credencial MinIO |

Si falta cualquiera, `__init__` lanza `ValueError` — el proceso muere antes de aceptar tráfico.

### Métodos

```python
def get_version(self, *, model_name: str, alias: str) -> str:
    # consulta el registry, devuelve el version string del alias
def online_predict(self, *, record: dict[str, Any]) -> float:
    # DataFrame de 1 fila → model.predict(df).iloc[0]
def batch_predict(self, *, records: list[dict[str, Any]]) -> list[float]:
    # DataFrame multi-fila → model.predict(df).tolist()
```

`online_predict` y `batch_predict` son **bloqueantes** (MLflow pyfunc es sync). Se llaman siempre desde `run_in_threadpool`.

### Carga del modelo al startup

`__init__` ejecuta `mlflow.pyfunc.load_model(model_uri)`. El modelo se carga **una sola vez** en memoria; no se recarga automáticamente si el alias `production` cambia en el registry. Para reflejar un nuevo modelo hace falta un restart del proceso.

## `AVMModelAdapter` ([services/prediction/adapters/avm_model_adapter.py](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py))

Implementa `ModelGateway`. Wrappea `ModelClient` y traduce entre `PredictionRequest` y el dict que MLflow espera.

- Hardcodea `model_name="bogota-avm"` y `alias="production"`.
- Serializa con `record.model_dump(mode='json', exclude={'property_id'})` — `property_id` no es feature del modelo.
- Llama `get_version(...)` en **cada predicción** para obtener el version string que se persiste con el registro — útil para auditoría aunque el modelo en memoria no cambie.

## Stack en docker-compose

| Servicio | Imagen | Puerto host | Notas |
|---|---|---|---|
| `mlflow` | mlflow:v3.12.0-full | 5000 | Backend store: SQLite en `/mlflow/mlflow.db` |
| `minio` | minio:RELEASE.2025-09-07 | 9000 (API), 9001 (console) | Artifact store S3-compatible |

`mlflow` usa `--default-artifact-root s3://mlflow-artifacts/` — el bucket **no** se crea automáticamente en MinIO. Crearlo manualmente desde http://localhost:9001 en dev local (ver [[analytics-service-local-dev]] gap #3).

## Relación con el pipeline de training

El training (`data/ml/AVM/`) loggea el modelo con `mlflow.pyfunc.log_model(...)` pero **no setea el alias `production`** — esa acción es manual/data team. Ver [[adr-model-promotion-external-to-service]].

El shape de features que MLflow espera coincide con `PredictionRequest` excluyendo `property_id`. Ver [[avm-training]] para los detalles del preprocesador.

## Claims

- `ModelClient.__init__` carga el modelo con `mlflow.pyfunc.load_model(model_uri)` — bloqueante, en startup ([mlflow/model.py:29](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L29)).
- `ModelClient.__init__` lanza `ValueError` si falta cualquiera de las 5 env vars ([mlflow/model.py:17-25](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L17-L25)).
- `online_predict` usa `.iloc[0]` (scalar), `batch_predict` usa `.tolist()` (lista) ([mlflow/model.py:36-40](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L36-L40)).
- `AVMModelAdapter` hardcodea `model_name="bogota-avm"` y `alias="production"` ([avm_model_adapter.py:9](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L9)).
- `property_id` se excluye del dict enviado a MLflow vía `exclude={'property_id'}` ([avm_model_adapter.py:11](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L11)).
- El bucket `mlflow-artifacts` no está en `MINIO_DEFAULT_BUCKETS` — no se crea automáticamente ([docker-compose.yml:127](docker-compose.yml#L127)).
- MLflow usa SQLite como backend store en `/mlflow/mlflow.db` dentro del container ([docker-compose.yml:146](docker-compose.yml#L146)).
