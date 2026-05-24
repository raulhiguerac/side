# Wiki — Índice

Wiki del monorepo `side`. Si es tu primera vez aquí, lee [CONVENTIONS.md](CONVENTIONS.md) antes de editar.

> **Estado actual:** piloto. Solo `analytics-service` tiene contenido. El patrón se valida durante 2-3 semanas antes de extenderlo a los demás servicios.

---

## Contenido transversal (`_shared/`)

- [glossary](wiki/_shared/glossary.md) — términos cross-cutting (AVM, IDECA, habímetro, Keycloak, MLflow, hex pattern, principal, POI, etc.)
- [architecture](wiki/_shared/architecture.md) — visión global del monorepo, hex pattern, patrones de comunicación (sync HTTP + async messaging), decisiones cross-cutting
- [dev-workflow](wiki/_shared/dev-workflow.md) — reglas de trabajo: discuss-before-code (CLAUDE.md) + pre-commit hook de wiki staleness
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

## catalog-service

- [catalog-service](wiki/catalog-service/catalog-service.md) — overview: 3 dominios (`catalog_admin`/`geo_catalog`/`geo_resolution`), routes, consumers, refactor pendiente de `/geo-resolution`
- [catalog-service-architecture](wiki/catalog-service/catalog-service-architecture.md) — layout interno, los 3 dominios, capa de integración, auth via cookie, caching de 3 capas para POIs

### domain/
- [catalog-service-catalog-admin](wiki/catalog-service/domain/catalog-service-catalog-admin.md) — writes: CRUD por entidad + bulk uploads (CSV barrios, GeoJSON polígonos), traductor de errores SQL→dominio, cache invalidation
- [catalog-service-geo-catalog](wiki/catalog-service/domain/catalog-service-geo-catalog.md) — reads para frontend: 5 UCs con patrón cache-aside uniforme + batch lookup multi-locality
- [catalog-service-poi-lifecycle](wiki/catalog-service/domain/catalog-service-poi-lifecycle.md) — POI side-effect only: 3 capas de dedup (cache+lock+FetchZone), lazy-fill de h3_cells, gap del read path no aprovechando el H3

### integrations/
- [catalog-service-mapbox](wiki/catalog-service/integrations/catalog-service-mapbox.md) — Mapbox Geocoder forward (deprecation pendiente post-refactor de `/geo-resolution`)
- [catalog-service-overpass](wiki/catalog-service/integrations/catalog-service-overpass.md) — Overpass QL, tag set actual + divergencia con tag set del training del AVM

### runbook/
- [catalog-service-local-dev](wiki/catalog-service/runbook/catalog-service-local-dev.md) — devcontainer + PostGIS DB, env vars completas, JWT via cookie, seed manual, 7 known gaps

### adrs/
- [ADR-0001 — PostGIS + h3 híbrido](wiki/catalog-service/adrs/adr-postgis-h3-hybrid.md)
- [ADR-0002 — AdminDivision de un solo nivel](wiki/catalog-service/adrs/adr-admin-division-single-level.md)
- [ADR-0003 — POI cache-aside, never on-demand](wiki/catalog-service/adrs/adr-poi-cache-aside.md)
- [ADR-0004 — GeoJSON upload pattern](wiki/catalog-service/adrs/adr-geojson-upload-pattern.md)
- [ADR-0005 — Mapbox solo en el frontend (catalog hace reverse-only)](wiki/catalog-service/adrs/adr-mapbox-frontend-only.md)

## frontend

- [frontend](wiki/frontend/frontend.md) — overview: scope funcional vs scaffolding, stack actual + deuda técnica reconocida, routes, consumers de servicios backend, roadmap
- [frontend-architecture](wiki/frontend/frontend-architecture.md) — layout interno, stores Pinia, composables, router guard, axios pattern, caching local, forms y mapas

### flows/
- [frontend-onboarding-flow](wiki/frontend/flows/frontend-onboarding-flow.md) — modal wizard de 4 pasos, state machine, persistencia dual server+client, refactor users-service ↔ catalog pendiente

### runbook/
- [frontend-local-dev](wiki/frontend/runbook/frontend-local-dev.md) — `npm run serve` port 8080, env vars, levantar backends a mano, 8 known gaps

### adrs/
- [ADR-0001 — Vue CLI hoy, migración a Vite diferida](wiki/frontend/adrs/adr-vue-cli-deferred-vite-migration.md)
- [ADR-0002 — Hash history para deployment en bucket estático](wiki/frontend/adrs/adr-hash-history-static-hosting.md)
- [ADR-0003 — Mapbox solo para geocoding, Leaflet+D3 para render](wiki/frontend/adrs/adr-mapbox-geocoding-leaflet-rendering.md)
- [ADR-0004 — Remover Firebase del frontend](wiki/frontend/adrs/adr-firebase-removal.md)

## Servicios pendientes (post-piloto)

- `properties-service` — core del producto, CRUD/feed/RBAC
- `users-service` — auth, perfiles

## avm (workload de ML)

Par del backend, conectado a `analytics-service` vía MLflow. Vive en `data/ml/AVM/` (fuera de `backend/`) por frontera de equipos (ver `[[adr-training-separated-from-runtime]]`).

- [avm-training](wiki/avm/avm-training.md) — pipeline de training: preprocesamiento, HPO con Optuna, registro en MLflow
