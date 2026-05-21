# Wiki — Índice

Wiki del monorepo `side`. Si es tu primera vez aquí, lee [CONVENTIONS.md](CONVENTIONS.md) antes de editar.

> **Estado actual:** piloto. Solo `analytics-service` tiene contenido. El patrón se valida durante 2-3 semanas antes de extenderlo a los demás servicios.

---

## Contenido transversal (`_shared/`)

- [glossary](wiki/_shared/glossary.md) — términos cross-cutting (AVM, IDECA, habímetro, Keycloak, MLflow, hex pattern, principal, POI, etc.)
- [architecture](wiki/_shared/architecture.md) — visión global del monorepo, hex pattern, patrones de comunicación (sync HTTP + async messaging), decisiones cross-cutting
- _shared/adrs/_:
  - [ADR-0001 — Auth vía Keycloak JWT](wiki/_shared/adrs/adr-auth-keycloak-jwt.md)
  - [ADR-0002 — Geo-enrichment at write time](wiki/_shared/adrs/adr-geo-enrichment-at-write-time.md)

## analytics-service (piloto)

- [analytics-service](wiki/analytics-service/analytics-service.md) — overview: dominios, consumers (sync + async), boundaries, stack, roadmap inmediato
- [analytics-service-architecture](wiki/analytics-service/analytics-service-architecture.md) — layout interno, dominios (prediction/market/shared), integraciones, persistencia, auth, workers

### domain/
- [analytics-service-prediction](wiki/analytics-service/domain/analytics-service-prediction.md) — schemas, UC `OnlinePrediction`, ports/adapters, errores, boundaries
- _analytics-service-glossary_ — términos específicos del servicio — _pendiente_

### flows/
- _training-pipeline_ — MLflow + MinIO end-to-end — _pendiente Día 4_
- _online-prediction_ — UC online actual — _pendiente Día 4_

### integrations/
- _mlflow_ — _pendiente Día 5_
- _minio_ — _pendiente Día 5_

### integrations/
- [analytics-service-mlflow](wiki/analytics-service/analytics-service-mlflow.md) — ModelClient, AVMModelAdapter, env vars MLflow, stack docker-compose

### workers/
- [analytics-service-kafka-consumer](wiki/analytics-service/workers/analytics-service-kafka-consumer.md) — ListingCreatedConsumer, diseño micro-batch 15 min, DLQ, group.id y scaling

### runbook/
- [analytics-service-local-dev](wiki/analytics-service/runbook/analytics-service-local-dev.md) — devcontainer first, infra del compose, env vars completas, 5 known gaps actuales

### adrs/
- [ADR-0001 — MLflow + MinIO como stack ML](wiki/analytics-service/adrs/adr-mlflow-minio-stack.md)
- [ADR-0002 — Training separado del runtime](wiki/analytics-service/adrs/adr-training-separated-from-runtime.md)
- [ADR-0003 — Promoción del modelo es externa al servicio](wiki/analytics-service/adrs/adr-model-promotion-external-to-service.md)

---

## Servicios pendientes (post-piloto)

- `properties-service` — core del producto, CRUD/feed/RBAC
- `catalog-service` — geo catalog, POIs
- `users-service` — auth, perfiles
- `frontend` — Vue 3, listing/detalle/publish

## avm (workload de ML)

Par del backend, conectado a `analytics-service` vía MLflow. Vive en `data/ml/AVM/` (fuera de `backend/`) por frontera de equipos (ver `[[adr-training-separated-from-runtime]]`).

- [avm-training](wiki/avm/avm-training.md) — pipeline de training: preprocesamiento, HPO con Optuna, registro en MLflow
