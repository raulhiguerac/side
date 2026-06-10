---
title: Pipeline de training del AVM
status: draft
last-verified: 2026-05-19
owners: [data]
related:
  - "[[analytics-service]]"
  - "[[analytics-service-prediction]]"
  - "[[analytics-service-mlflow]]"
  - "[[architecture]]"
  - "[[adr-lightgbm-log-target]]"
  - "[[adr-optuna-hpo-reproducibility]]"
  - "[[adr-geospatial-feature-engineering]]"
sources: [../../sources/analytics-service/2026-05-19-foundational-qa.md]
---

## TL;DR

Pipeline de training del modelo AVM (Automated Valuation Model) para precios de venta en Bogotá. Vive en `data/ml/AVM/` (fuera de `backend/`) por frontera de equipos: data team experimenta y entrena, runtime team (`analytics-service`) solo consume el modelo via MLflow. LightGBM regresor + Optuna para HPO. La promoción a alias `production` es **manual** y NO la hace el training.

## Por qué separado del backend

Ver `[[adr-training-separated-from-runtime]]`. Resumen: data team ≠ runtime team. MLflow es el contrato entre ambos lados.

## Entry point

CLI: `python data/ml/AVM/training/train.py` con args obligatorios:

| Arg | Para qué |
|---|---|
| `--data-path` | CSV con propiedades + columna `price` |
| `--poi-path` | CSV de POIs (extraído de OpenStreetMap hoy) |
| `--feature-schema-path` | JSON con schema (features, target, validations) |
| `--experiment-name` | Nombre del experiment en MLflow |
| `--model-name` | Nombre del modelo en el MLflow registry |

Env vars requeridas (validadas al inicio): `MLFLOW_TRACKING_URI`, `MLFLOW_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.

## Pipeline

```
load_and_preprocess  →  validate  →  split_data  →  tune_with_optuna  →  final_train
```

Cada paso implementado en `data/ml/AVM/training/pipeline/`. La función orquestadora es `run_train_pipeline` en [train.py](data/ml/AVM/training/train.py).

### 1. `load_and_preprocess` ([pipeline/data.py](data/ml/AVM/training/pipeline/data.py))
- Lee `data.csv` y `pois.csv` con pandas.
- Calcula `md5` del archivo POI (auditoría — queda como `poi_md5` en el run).
- Fit del `AVMPreprocessor` sobre los POIs.
- Aplica `target = log10(price)` (transformación log para reducir varianza).
- Aplica `preprocessor.transform_batch(records=df)` para generar todas las features.

### 2. `validate`
Chequeos contra el schema JSON:
- Todas las columnas requeridas presentes.
- `target > 0`.
- Total de columnas matchea `validations.number_cols` (catch para drift accidental del schema).
- Sin nulos en columnas requeridas.
- `estrato` en `[validations.estrato.min, validations.estrato.max]`.
- `area_m2_log > validations.area_m2_log.min_exclusive`.

### 3. `split_data` ([train.py:17-31](data/ml/AVM/training/train.py#L17-L31))
- 70 / 15 / 15 (train / val / test) usando `sklearn.train_test_split`.
- **Stratified por `tipo_propiedad`** (`apartment` vs `house`) en ambos splits.
- `random_state=42` fijo.

### 4. `tune_with_optuna` ([pipeline/tuner.py](data/ml/AVM/training/pipeline/tuner.py))
- Optuna con `TPESampler(seed=42)`, **400 trials**.
- Objetivo: minimizar RMSE en val set.
- Logueado a MLflow bajo un run separado `optuna_fine_tuning`.

Hiperparámetros buscados:

| Param | Rango |
|---|---|
| `num_leaves` | int [31, 255] |
| `learning_rate` | float [0.01, 0.1] log |
| `max_depth` | int [4, 12] |
| `min_child_samples` | int [10, 100] |
| `feature_fraction` | float [0.5, 1.0] |
| `bagging_fraction` | float [0.5, 1.0] |
| `bagging_freq` | int [1, 7] |
| `reg_alpha` | float [1e-8, 10.0] log |
| `reg_lambda` | float [1e-8, 10.0] log |

LightGBM con early stopping de 50 rounds, max 2000 boost rounds.

### 5. `final_train` ([pipeline/trainer.py](data/ml/AVM/training/pipeline/trainer.py))
- Toma los `best_params` de Optuna.
- Re-entrena en train para encontrar `best_rounds` con early stopping en val.
- **Re-entrena en train+val combinados** con esos `best_rounds` (sin val) → modelo final.
- Evalúa en test: RMSE en escala log, MAPE en escala $ COP real.
- Loggea todo a MLflow bajo run `final_model`.

## El preprocesador (`AVMPreprocessor`)

Archivo: [preprocessor.py](data/ml/AVM/training/preprocessor.py). Stateful — se entrena (fit) y se serializa con joblib (`preprocessor.pkl`) como artifact del modelo. Se carga en el path de inferencia junto al booster.

### Pipeline de features (`transform_batch`)
```
encode_base_features  →  add_h3  →  poi_transformer.transform  →  add_landmark_distances  →  cast_categoricals
```

#### `encode_base_features` ([transforms/encoders.py](data/ml/AVM/training/transforms/encoders.py))
- Renombra columnas inglés → español: `bedrooms→cuartos`, `bathrooms→banios`, `parking_spots→parqueaderos`, `stratum→estrato`, `property_type→tipo_propiedad`.
- Deriva `antiguedad` (bins: `menor a 1 año`, `1 a 8 años`, `9 a 15 años`, `16 a 30 años`, `más de 30 años`, `sin especificar`).
- Deriva `area_m2_log = log10(area_m2)`, `bedroom_m2 = cuartos / area_m2`, `bathroom_bedroom = banios / cuartos`.
- Mapea `tipo_propiedad` a int (`apartment=0`, `house=1`).

#### `add_h3`
3 columnas de H3 cells (Uber's H3 spatial index) en resoluciones 6, 7, 8 → `h3_r6`, `h3_r7`, `h3_r8`. Indexa el listing en hexágonos a 3 niveles de granularidad.

#### `PoiTransformer` ([transforms/poi.py](data/ml/AVM/training/transforms/poi.py))
- **fit**: categoriza POIs según mapeos en `feature_store/constants.py` (transport, food, education, health, finance, commerce, recreation, worship, leisure, fashion, home, electronics, auto, services, adult). Reporta uncategorized %. Construye `BallTree(haversine)` con coords de POIs.
- **transform**: para cada radio (0.3 km, 0.8 km, 1.2 km) y categoría, cuenta POIs cercanos al listing → columnas `poi_300m_<cat>`, `poi_800m_<cat>`, `poi_1200m_<cat>`.

#### `add_landmark_distances` ([transforms/landmarks.py](data/ml/AVM/training/transforms/landmarks.py))
Distancia haversine (km) a 12 landmarks de Bogotá hardcodeados en `feature_store/constants.py:BOGOTA_LANDMARKS`:

Andino, Gran Estación, Titán Plaza, Portal Norte TM, Portal Sur TM, Portal 80 TM, U Andes, U Nacional, Centro Internacional, Parque Simón Bolívar, Parque Virrey, Aeropuerto El Dorado.

#### `cast_categoricals`
Castea las columnas listadas en `schema.cat_cols` al dtype `category` de pandas. LightGBM las consume nativamente sin one-hot.

## El modelo (`AVM`)

[avm_model.py](data/ml/AVM/training/avm_model.py) define `AVM(mlflow.pyfunc.PythonModel)` — wrapper de inferencia que MLflow carga:

```python
class AVM(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.preprocessor = joblib.load(context.artifacts["preprocessor"])
        self.booster = lgb.Booster(model_file=context.artifacts["booster"])

    def predict(self, context, model_input: pd.DataFrame) -> pd.Series:
        df = self.preprocessor.transform_batch(model_input)
        return pd.Series(10 ** self.booster.predict(df))
```

Recibe el request **crudo** (sin features derivadas) y aplica el preprocesador antes de inferir. Devuelve `10 ** booster.predict(...)` para revertir la transformación log y entregar el precio en $ COP.

## Contenido de cada run de MLflow

### Params
- Hiperparámetros finales (incluyendo seeds fijas).
- `best_rounds` (de early stopping).
- `train_size`, `val_size`, `test_size`.
- `n_features`, `n_poi_features`, `n_dist_features`.
- `poi_md5` — auditoría del archivo de POIs.

### Metrics
- `target_mean`, `target_std`, `target_min`, `target_max` (estadísticas del target en train).
- `test_rmse` (escala log10).
- `test_mape` (escala $ COP real, % de error medio).

### Artifacts
- `preprocessor.pkl` (state del preprocesador con joblib).
- `booster.txt` (modelo LightGBM serializado).
- `feature_schema.json` (snapshot del schema usado en este run — traceabilidad).
- `code_paths`: copia del código necesario para deserializar (`avm_model.py`, `preprocessor.py`, `transforms/`, `feature_store/`).
- `input_example`: ejemplo de request crudo.
- `signature`: inferida del input_example + un Series `price` ejemplo.

El modelo queda registrado en el MLflow registry con el `--model-name` pasado por CLI.

## Promoción a `production`

**El training NO setea el alias `production`.** Esa decisión es del data team, manual, vía MLflow UI o CLI. Ver `[[adr-model-promotion-external-to-service]]`.

Flujo esperado (informal hoy):
1. Data team entrena → registra nueva versión del modelo.
2. Compara métricas vs versión actual de `production`.
3. Si es mejor, mueve el alias `production` a la versión nueva.
4. `analytics-service` lee el nuevo modelo en su próximo startup. _Pendiente confirmar si hay hot reload o requiere restart._

## Schema-driven design

Todo el pipeline está parametrizado por el JSON schema en `--feature-schema-path`. Estructura mínima esperada:

```json
{
  "target": "price_log",
  "features": ["...lista de columnas usadas como features..."],
  "cat_cols": ["...subset de features que son categóricas..."],
  "validations": {
    "number_cols": 70,
    "estrato": {"min": 1, "max": 6},
    "area_m2_log": {"min_exclusive": 0}
  }
}
```

Permite versionar el contrato de features sin tocar el código del pipeline. Una nueva versión del modelo puede agregar/quitar features cambiando solo el JSON (y el código que los produce si aplica).

## Inputs del modelo en inferencia

El input que MLflow espera matchea el shape de `PredictionRequest` (menos `property_id`). Ver [[analytics-service-prediction]] para los rangos válidos.

El `input_example` del run de MLflow:
```python
{
    "area_m2": 72.0, "bedrooms": 3, "bathrooms": 2.0, "parking_spots": 1,
    "stratum": 4, "property_type": "apartment", "year_built": 2012,
    "lat": 4.65, "lon": -74.08, "barrio_ideca": "CHICO NORTE",
}
```

## Boundaries — lo que el training **NO** hace

- **No promueve modelos** — la decisión de qué versión sirve queda en el data team.
- **No se redespliega** — `analytics-service` lo consume vía MLflow, no se republica el container.
- **No procesa requests live** — eso pasa por el adapter de MLflow en analytics-service, sin HTTP layer aquí.
- **No tiene CI hoy** — se corre manualmente. Futuro: Airflow u otro orchestrator.

## Decisiones registradas (ADRs)

- [[adr-lightgbm-log-target]] — LightGBM, target `log10(price)`, categóricas nativas sin one-hot.
- [[adr-optuna-hpo-reproducibility]] — Optuna TPE 400 trials, seeds fijas, refit train+val.
- [[adr-geospatial-feature-engineering]] — H3 multi-res + POIs por radio + distancias a landmarks, schema-driven.

## Open items

- Automatizar el run vía orchestrator (Airflow probable).
- Decidir trigger del re-entreno: cron mensual / data drift / volumen acumulado de nuevos listings.
- Validar que el container de `analytics-service` toma el nuevo alias `production` sin restart explícito.
- Migrar POIs de CSV manual a tabla poblada por `catalog-service` → eventualmente DWH.
- Considerar versionar el feature schema JSON en el repo junto al pipeline.

## Claims

- El target del modelo es `log10(price)`, no `price` directo ([data.py:22](data/ml/AVM/training/pipeline/data.py#L22)).
- El split es 70/15/15 stratified por `tipo_propiedad` ([train.py:23-29](data/ml/AVM/training/train.py#L23-L29)).
- Optuna corre 400 trials con TPE sampler ([tuner.py:62](data/ml/AVM/training/pipeline/tuner.py#L62)).
- Tras el tuning, el modelo final re-entrena en train+val combinados con los `best_rounds` que vinieron de early stopping en val ([trainer.py:68-93](data/ml/AVM/training/pipeline/trainer.py#L68-L93)).
- El modelo en MLflow es un `mlflow.pyfunc` custom que envuelve preprocesador + booster ([trainer.py:117](data/ml/AVM/training/pipeline/trainer.py#L117), [avm_model.py:6](data/ml/AVM/training/avm_model.py#L6)).
- POIs se contabilizan en 3 radios — 300 m, 800 m, 1200 m ([feature_store/constants.py:33](data/ml/AVM/training/feature_store/constants.py#L33)).
- H3 hexagons se generan en 3 resoluciones — 6, 7, 8 ([feature_store/constants.py:31](data/ml/AVM/training/feature_store/constants.py#L31)).
- Hay 12 landmarks de Bogotá hardcodeados que producen 12 features `dist_<landmark>` ([feature_store/constants.py:3-16](data/ml/AVM/training/feature_store/constants.py#L3-L16)).
- Las categorías de POIs se construyen desde mapeos sobre tags de OSM (`amenity`, `shop`, `public_transport`, `leisure`, `healthcare`) — listados en `feature_store/constants.py`.
- El `poi_md5` se loggea como param en cada run para auditar contra qué POIs se entrenó cada modelo ([trainer.py:90](data/ml/AVM/training/pipeline/trainer.py#L90)).
- LightGBM consume las categóricas nativamente vía `cast_categoricals` — no hay one-hot encoding ([encoders.py:51-54](data/ml/AVM/training/transforms/encoders.py#L51-L54)).
- El modelo NO incluye `property_id` como feature — se excluye en el adapter al hacer la llamada ([avm_model_adapter.py:11](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L11)).
- El training NO setea el alias `production` — esa acción es manual, fuera del pipeline.
- Existe `catboost` en las dependencies (`pyproject.toml`) pero el pipeline actual usa solo LightGBM.
