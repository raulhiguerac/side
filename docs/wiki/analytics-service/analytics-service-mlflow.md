---
title: MLflow en analytics-service
status: draft
last-verified: 2026-07-13
owners: [analytics-service]
related:
  - "[[analytics-service]]"
  - "[[analytics-service-architecture]]"
  - "[[avm-training]]"
  - "[[adr-mlflow-minio-stack]]"
sources: [../../sources/analytics-service/2026-05-19-foundational-qa.md, ../../sources/analytics-service/2026-05-20-prediction-wiring-and-batch-uc.md, ../../sources/frontend/2026-05-29-avm-form-wiring-predict.md]
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

## Gotcha: schema MLflow y campos nullable

El schema de input del modelo se infiere con `infer_signature(input_example, ...)` en el momento del registro. Si `input_example` tiene `year_built: 2012` (int no nulo), MLflow marca el campo como `long required`. La validación del schema **corre antes** del preprocessing del modelo pyfunc — por eso `None` es rechazado aunque `_year_to_antiguedad` en el preprocessor maneja `None → 'sin especificar'` correctamente.

**Síntoma:** `Can not safely convert object to int64` al llamar `/predict` con `year_built: null`.

**Fix correcto:** re-registrar el modelo con `year_built: None` en `_make_raw_input_example()` (`data/ml/AVM/training/pipeline/trainer.py`) para que MLflow infiera el campo como nullable. Esto requiere correr `final_train` de nuevo y promover el nuevo modelo al alias `production`.

**Workaround temporal:** en `AVMModelAdapter.online_predict`, reemplazar `year_built: None` con `0` después del `model_dump` — pasa la validación del schema y `_year_to_antiguedad(0)` devuelve `'sin especificar'` (2026 años de antigüedad cae fuera de todos los bins).

## Stack en docker-compose

| Servicio | Imagen | Puerto host | Notas |
|---|---|---|---|
| `mlflow` | mlflow:v3.12.0-full | 5000 | Backend store: SQLite en `/mlflow/mlflow.db` |
| `minio` | minio:RELEASE.2025-09-07 | 9000 (API), 9001 (console) | Artifact store S3-compatible |

`mlflow` usa `--default-artifact-root s3://mlflow-artifacts/`. Desde el 2026-09-07 el bucket lo crea el servicio `minio-init` del compose, junto con el usuario `side-mlflow-dev` cuya policy `mlflow` da acceso solo a ese bucket.

## Relación con el pipeline de training

El training (`data/ml/AVM/`) loggea el modelo con `mlflow.pyfunc.log_model(...)` pero **no setea el alias `production`** — esa acción es manual/data team. Ver [[adr-model-promotion-external-to-service]].

El shape de features que MLflow espera coincide con `PredictionRequest` excluyendo `property_id`. Ver [[avm-training]] para los detalles del preprocesador.

## Claims

- `ModelClient.__init__` carga el modelo con `mlflow.pyfunc.load_model(model_uri)` — bloqueante, en startup ([mlflow/model.py:29](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L29)).
- `ModelClient.__init__` lanza `ValueError` si falta cualquiera de las 5 env vars ([mlflow/model.py:17-25](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L17-L25)).
- `online_predict` usa `.iloc[0]` (scalar), `batch_predict` usa `.tolist()` (lista) ([mlflow/model.py:36-40](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L36-L40)).
- `AVMModelAdapter` hardcodea `model_name="bogota-avm"` y `alias="production"` ([avm_model_adapter.py:11,16](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L11-L16)).
- `property_id` se excluye del dict enviado a MLflow vía `exclude={'property_id'}` ([avm_model_adapter.py:12,17](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L12-L17)).
- El bucket `mlflow-artifacts` y el usuario `side-mlflow-dev` los crea `minio-init`; la policy incluye `ListBucket` y las acciones de multipart, que el SDK de MLflow necesita ([infra/minio/policies/mlflow-artifacts-policy.json](infra/minio/policies/mlflow-artifacts-policy.json)).
- `mlflow-init` (2026-09-07) siembra el registro y los artifacts antes de que arranque el server: copia `infra/mlflow/registry/mlflow.db` al volumen `mlflow_data` y espeja `infra/mlflow/artifacts/` a `s3://mlflow-artifacts/`. Ambos pasos tienen centinela y no pisan nada existente ([infra/dev/mlflow-init.sh](infra/dev/mlflow-init.sh)).
- Se restaura el sqlite en vez de registrar por API porque el `MLmodel` del modelo trae horneados `artifact_path` (`s3://mlflow-artifacts/3/models/m-62a127.../artifacts`), `model_id` y `run_id`: registrar por API generaria ids nuevos que no coinciden con los del propio artefacto. Por eso los artifacts se restauran preservando el prefijo `3/`.
- `mc mirror` **no** salta los objetos ya presentes: falla con `Overwrite not allowed` y aun asi devuelve exit 0, asi que `mlflow-init` cuenta los objetos del prefijo antes y despues en vez de confiar en el codigo de salida.
- MLflow usa SQLite como backend store en `/mlflow/mlflow.db` dentro del container ([docker-compose.yml:156](docker-compose.yml#L156)).
- El schema de MLflow se infiere de `input_example` en `final_train` — si `year_built` es no nulo en el ejemplo, MLflow lo marca `long required` y rechaza `null` en runtime antes de que corra el preprocessing ([trainer.py](data/ml/AVM/training/pipeline/trainer.py)).
- `_year_to_antiguedad(None)` devuelve `'sin especificar'` correctamente, pero la validación del schema MLflow rechaza `null` antes de llegar al preprocessor ([transforms/encoders.py:18-20](data/ml/AVM/training/transforms/encoders.py#L18-L20)).
- Fix correcto: re-registrar con `year_built: None` en `_make_raw_input_example()` para que el schema sea nullable — requiere nuevo `final_train` y promoción manual al alias `production` ([trainer.py](data/ml/AVM/training/pipeline/trainer.py)).
