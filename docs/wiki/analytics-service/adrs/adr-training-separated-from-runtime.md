---
title: ADR-0002 — Training separado del runtime
status: stable
last-verified: 2026-06-20
owners: [analytics-service]
related:
  - "[[architecture]]"
  - "[[analytics-service]]"
  - "[[avm-training]]"
  - "[[adr-mlflow-minio-stack]]"
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
decision-date: 2026-05-19
decision-status: accepted
---

# ADR-0002 — Training separado del runtime

## Contexto

Dos roles distintos en el ciclo de vida del modelo AVM:

- **Data team** — experimenta, hace EDA, prueba features, entrena modelos, define el feature schema.
- **Runtime team** — opera `analytics-service`, monitorea SLA, maneja incidentes, sirve predicciones.

Hoy ambos roles los cubre la misma persona, pero el diseño anticipa el split (team growth previsto para julio-agosto 2026). Sin separación, las velocidades de evolución se acoplan: el data team no puede iterar sin pedir review del runtime, y el runtime carga la complejidad de training en su path crítico.

## Decisión

El código de training vive en `data/ml/AVM/`, **fuera de `backend/analytics-service/`**. El servicio analytics no importa nada de `data/ml/`. La comunicación entre ambos lados ocurre **exclusivamente vía MLflow** (model registry + artifact store + `production` alias).

## Alternativas consideradas

- **Training como subpaquete del servicio** (`backend/analytics-service/training/`) — más cohesión inicial pero acopla las velocidades de evolución; PRs de training pasan por review del runtime.
- **Training en repo separado** — máxima independencia pero rompe la atomicidad del monorepo y dificulta cambios coordinados de feature contract (ej. agregar una feature requiere PRs en 2 repos).
- **Notebook puro + script de export** — más pesado de mantener, sin estructura clara.

## Consecuencias

- ✅ Data team puede iterar sin tocar el servicio (no necesita PR review de runtime).
- ✅ MLflow como contrato es testeable independientemente (un modelo registrado se puede validar sin levantar el servicio).
- ✅ El monorepo permite cambios coordinados cuando hace falta (un solo commit puede tocar training + service + schema).
- ❌ Cambios coordinados (ej. agregar una feature) requieren editar 2 lugares + actualizar el JSON schema.
- ❌ Hoy el servicio carga deps pesadas de ML (LightGBM, scikit-learn, geopandas, pandas) en su `pyproject.toml` aunque las use poco — pendiente limpiar.
- ❌ `data/ml/AVM/training/` no tiene su propio `pyproject.toml` todavía; comparte el env del monorepo.

## Claims

- `data/ml/AVM/training/train.py` es un CLI invocable directamente, sin importar nada de `backend/`.
- `analytics-service` no importa nada de `data/ml/` (verificable con grep desde `backend/analytics-service/`).
- MLflow es el único punto de contacto entre training y runtime — no hay sharing de código, archivos pickled cross-repo, ni APIs HTTP directas.
- Los `code_paths` que se loggean en MLflow (`avm_model.py`, `preprocessor.py`, `transforms/`, `feature_store/`) viajan **dentro del artifact**, no se importan en runtime ([trainer.py:125-130](data/ml/AVM/training/pipeline/trainer.py#L125-L130)).
