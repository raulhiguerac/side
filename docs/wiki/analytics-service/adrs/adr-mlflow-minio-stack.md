---
title: ADR-0001 — MLflow + MinIO como stack ML
status: stable
last-verified: 2026-05-19
owners: [analytics-service]
related:
  - "[[analytics-service-architecture]]"
  - "[[avm-training]]"
  - "[[analytics-service-mlflow]]"
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
decision-date: 2026-05-19
decision-status: accepted
---

# ADR-0001 — MLflow + MinIO como stack ML

## Contexto

Necesitamos tres capacidades para el ciclo de vida del modelo AVM:
1. **Tracking** de experimentos de training (params, métricas, artifacts, lineage).
2. **Artifact storage** (modelos serializados, preprocesador, schemas, plots).
3. **Model registry** con aliases semánticos (`production`, `staging`) y versioning.

Restricciones:
- Sin créditos en ninguna nube (Colombia, fase pre-revenue).
- Stack agnóstico — debe correr en cualquier docker host.
- El data team debe poder experimentar sin pedirle setup al runtime team.

## Decisión

- **MLflow self-hosted** como tracking + registry + serving (vía `mlflow.pyfunc.PythonModel` custom).
- **MinIO self-hosted** como artifact store, configurado como S3 endpoint (`MLFLOW_S3_ENDPOINT_URL`).
- `analytics-service` consume el modelo vía un adapter MLflow leyendo del alias `production`.

## Alternativas consideradas

- **SageMaker / Vertex AI / Databricks** — managed end-to-end pero requieren créditos cloud y atan al proveedor.
- **BentoML** — excelente para serving + packaging pero más débil para tracking y registry.
- **Weights & Biases** — el mejor tracking del mercado, pero registry/serving requieren W&B Enterprise.
- **Stack custom** (Postgres + S3 + scripts propios) — máxima portabilidad pero re-implementar tooling estándar.

## Consecuencias

- ✅ Stack estándar de la industria — fácil encontrar gente que ya lo conoce.
- ✅ Tracking + registry + serving en un solo sistema cohesivo.
- ✅ MLflow + MinIO corren en cualquier docker host (incluyendo el devcontainer).
- ✅ MinIO permite migrar a S3 real cambiando un endpoint URL.
- ❌ MLflow no es trivial de operar a escala (DB propia, upgrades, scaling).
- ❌ MinIO está bien para dev/staging pero a producción real conviene reevaluar (S3 directo, GCS, Azure Blob).
- ❌ La UI de MLflow es funcional pero limitada — sin RBAC granular ni dashboards avanzados sin MLflow Enterprise.

## Claims

- El servicio carga el modelo en `ModelClient.__init__` desde el URI configurado en `MLFLOW_MODEL_URI` ([mlflow/model.py:29](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L29)).
- 5 env vars son obligatorias en startup del cliente MLflow: `MLFLOW_TRACKING_URI`, `MLFLOW_S3_ENDPOINT_URL`, `MLFLOW_MODEL_URI`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` ([mlflow/model.py:11-23](backend/analytics-service/src/app/integrations/ml/mlflow/model.py#L11-L23)).
- El stack es S3-compatible vía MinIO — el código usa boto3 transparente vía MLflow.
