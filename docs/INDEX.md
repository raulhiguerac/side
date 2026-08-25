# Wiki — Índice

Wiki del monorepo `side`. Si es tu primera vez aquí, lee [CONVENTIONS.md](CONVENTIONS.md) antes de editar.

> **Estado actual:** el piloto arrancó en `analytics-service` (2026-05-19) y, tras validar el patrón, se extendió a `catalog-service`, `frontend`, `properties-service` y `users-service`. Todos los microservicios del backend + el frontend + el workload `avm` están documentados (desde 2026-05-28); última pasada de verificación contra código: 2026-06-12.

---

## Contenido transversal (`_shared/`)

- [glossary](wiki/_shared/glossary.md) — términos cross-cutting (AVM, IDECA, habímetro, Keycloak, MLflow, hex pattern, principal, POI, etc.)
- [architecture](wiki/_shared/architecture.md) — visión global del monorepo, hex pattern, patrones de comunicación (sync HTTP + async messaging), decisiones cross-cutting
- [dev-workflow](wiki/_shared/dev-workflow.md) — reglas de trabajo: discuss-before-code (CLAUDE.md) + pre-commit hook de wiki staleness
- [open-items](wiki/_shared/open-items.md) — backlog vivo de gaps y deuda técnica cross-service (checklist marcable entre sesiones)
- [project-roadmap-2026](wiki/_shared/project-roadmap-2026.md) — fases del producto: completado (catálogo, users, AVM), en progreso (properties), pendiente (infra K3s, heatmap DWH, notifications-ms, payments-ms)
- [business-model](wiki/_shared/business-model.md) — monetización por fases (promocionados, comisiones, B2B data, FinTech), análisis competitivo (Cerouno, Rentpana, Habi), moat y features planeadas
- _shared/adrs/_:
  - [ADR-0001 — Auth vía Keycloak JWT](wiki/_shared/adrs/adr-auth-keycloak-jwt.md)
  - [ADR-0002 — Geo-enrichment at write time](wiki/_shared/adrs/adr-geo-enrichment-at-write-time.md)
  - [ADR-0003 — Resolución H3 por caso de uso, celdas no reusables entre fronteras](wiki/_shared/adrs/adr-h3-resolution-per-use-case.md)
  - [ADR-0004 — Impresiones y clicks vía beacon de cliente + collector + Kafka](wiki/_shared/adrs/adr-impressions-beacon-pipeline.md)
  - [ADR-0005 — Cache como capa opcional; degradación silenciosa a DB](wiki/_shared/adrs/adr-cache-optional-layer.md)
  - [ADR-0006 — Librería interna compartida para clientes de infra (Redis/MinIO)](wiki/_shared/adrs/adr-shared-infra-lib.md)

## analytics-service (piloto)

- [analytics-service](wiki/analytics-service/analytics-service.md) — overview: dominios, consumers (sync + async), boundaries, stack, roadmap inmediato
- [analytics-service-architecture](wiki/analytics-service/analytics-service-architecture.md) — layout interno, dominios (prediction/market/shared), integraciones, persistencia, auth, workers

### domain/
- [analytics-service-prediction](wiki/analytics-service/domain/analytics-service-prediction.md) — schemas, UC `OnlinePrediction`, ports/adapters, errores, boundaries
- _analytics-service-glossary_ — términos específicos del servicio — _pendiente_

### flows/
- _training-pipeline_ — MLflow + MinIO end-to-end — _pendiente_
- _online-prediction_ — UC online actual — _pendiente_

### integrations/
- [analytics-service-mlflow](wiki/analytics-service/analytics-service-mlflow.md) — ModelClient, AVMModelAdapter, env vars MLflow + MinIO, stack docker-compose

### workers/
- [analytics-service-kafka-consumer](wiki/analytics-service/workers/analytics-service-kafka-consumer.md) — ListingCreatedConsumer, diseño micro-batch 15 min, DLQ, group.id y scaling

### runbook/
- [analytics-service-local-dev](wiki/analytics-service/runbook/analytics-service-local-dev.md) — devcontainer first, infra del compose, env vars completas, 5 known gaps actuales
- [analytics-service-testing](wiki/analytics-service/runbook/analytics-service-testing.md) — 63 unit tests, setup con `uv sync --extra dev`, patrones de mock (fake_threadpool, AsyncMock/MagicMock, consumer fixture)

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
- [catalog-service-overpass](wiki/catalog-service/integrations/catalog-service-overpass.md) — Overpass QL, tag set unificado con AVM (5 keys OSM, 15 categorías, category_map.py)
- [catalog-service-ors](wiki/catalog-service/integrations/catalog-service-ors.md) — OpenRouteService self-hosted, setup docker, paths nightly v9, isócronas

### runbook/
- [catalog-service-local-dev](wiki/catalog-service/runbook/catalog-service-local-dev.md) — devcontainer + PostGIS DB, env vars completas, JWT via cookie, seed manual, 7 known gaps

### adrs/
- [ADR-0001 — PostGIS + h3 híbrido](wiki/catalog-service/adrs/adr-postgis-h3-hybrid.md)
- [ADR-0002 — AdminDivision de un solo nivel](wiki/catalog-service/adrs/adr-admin-division-single-level.md)
- [ADR-0003 — POI cache-aside, never on-demand](wiki/catalog-service/adrs/adr-poi-cache-aside.md)
- [ADR-0004 — GeoJSON upload pattern](wiki/catalog-service/adrs/adr-geojson-upload-pattern.md)
- [ADR-0005 — Mapbox solo en el frontend (catalog hace reverse-only)](wiki/catalog-service/adrs/adr-mapbox-frontend-only.md)
- [ADR-0006 — Isócronas con ORS + H3 para reachable POIs](wiki/catalog-service/adrs/adr-isochrone-ors-h3.md)

## frontend

- [frontend](wiki/frontend/frontend.md) — overview: scope funcional vs scaffolding, stack actual + deuda técnica reconocida, routes, consumers de servicios backend, roadmap
- [frontend-architecture](wiki/frontend/frontend-architecture.md) — layout interno, stores Pinia, composables, router guard, axios pattern, caching local, forms y mapas
- [frontend-map-component](wiki/frontend/frontend-map-component.md) — componente de mapa dumb/reusable (MapUser): vue-leaflet declarativo, markers-prop + slot, defineModel zoom, iconos data-driven, D3 plug-and-play

### flows/
- [frontend-onboarding-flow](wiki/frontend/flows/frontend-onboarding-flow.md) — modal wizard de 4 pasos, state machine, persistencia dual server+client, refactor users-service ↔ catalog pendiente
- [frontend-poi-reachable](wiki/frontend/flows/frontend-poi-reachable.md) — sección "Cerca del lugar": useReachablePois (1 POST × 9 resultados), acordeón por rango, isocronas + cluster markers, CATEGORY_META/PRIORITY; spinner v-show + resize fix para Leaflet
- [frontend-property-create-form](wiki/frontend/flows/frontend-property-create-form.md) — form multi-step 4 pasos (Tipo/Detalles/Ubicación/Imágenes), patrón update:form, Google Places + NearbyPlaces en step 2, previewId UUID
- [frontend-property-edit-form](wiki/frontend/flows/frontend-property-edit-form.md) — vista de edición en 2 columnas, split en 5 tarjetas presentacionales, campos fijos vs editables, gotcha de `Decimal` serializado como string
- [frontend-admin-panel](wiki/frontend/flows/frontend-admin-panel.md) — panel admin embebido: nav gating, rutas `requiresAdmin`, fix de race en el guard, hub view, tabs como rutas hijas, modal de bulk upload en 3 pasos (presigned PUT), tabla de moderación + panel de vista previa, 4 de 23 endpoints cableados

### runbook/
- [frontend-local-dev](wiki/frontend/runbook/frontend-local-dev.md) — `npm run serve` port 8080, env vars, levantar backends a mano, 10 known gaps

### adrs/
- [ADR-0001 — Vue CLI hoy, migración a Vite diferida](wiki/frontend/adrs/adr-vue-cli-deferred-vite-migration.md)
- [ADR-0002 — Hash history para deployment en bucket estático](wiki/frontend/adrs/adr-hash-history-static-hosting.md)
- [ADR-0003 — Mapbox solo para geocoding, Leaflet+D3 para render](wiki/frontend/adrs/adr-mapbox-geocoding-leaflet-rendering.md)
- [ADR-0004 — Remover Firebase del frontend](wiki/frontend/adrs/adr-firebase-removal.md)
- [ADR-0005 — Google Maps Places API (New) para geocoding](wiki/frontend/adrs/adr-gmaps-places-geocoding.md)
- [ADR-0006 — Campos fijos vs. editables al editar una propiedad](wiki/frontend/adrs/adr-property-edit-fixed-fields.md)
- [ADR-0007 — Sin librería de componentes: la tabla admin se construye a mano](wiki/frontend/adrs/adr-no-component-library.md)
- [ADR-0008 — TanStack Table (headless) para la tabla admin](wiki/frontend/adrs/adr-tanstack-table.md)
- [ADR-0009 — Las tabs del panel admin son rutas hijas, no un switch de componentes](wiki/frontend/adrs/adr-admin-tabs-nested-routes.md)
- [ADR-0010 — Moderar se hace en el panel de vista previa, con un formulario de guardado explícito](wiki/frontend/adrs/adr-moderation-panel-staged-form.md)
- [ADR-0011 — Promocionar vive en su propia sub-tab, no en el panel de moderación](wiki/frontend/adrs/adr-promotions-own-subtab.md)
- [ADR-0012 — Los filtros del panel admin viven en la URL, no en el composable](wiki/frontend/adrs/adr-admin-filters-in-query-params.md)

## properties-service

- [properties-service](wiki/properties-service/properties-service.md) — overview: 3 dominios (`listing`/`search`/`admin`), feed público, panel admin, sin worker Kafka hoy
- [properties-service-architecture](wiki/properties-service/properties-service-architecture.md) — layout interno, 5 tablas (PostGIS + H3), DI, integraciones, auth por cookie

### domain/
- [properties-service-listing](wiki/properties-service/domain/properties-service-listing.md) — CRUD del dueño + flujo de imágenes presigned/batch + visibilidad
- [properties-service-search](wiki/properties-service/domain/properties-service-search.md) — feed orgánico+ads con fallback de preferencias + feed-mapa por H3
- [properties-service-admin](wiki/properties-service/domain/properties-service-admin.md) — moderación (state machine), precios estimados dual, promociones, encolado del bulk import + historial de imports
- [properties-service-bulk-create-worker](wiki/properties-service/domain/properties-service-bulk-create-worker.md) — import async end-to-end: presigned PUT, BackgroundTasks con sesión propia, persistencia por chunk de 2500, cierre del BulkJob

### integrations/
- [properties-service-catalog](wiki/properties-service/integrations/properties-service-catalog.md) — geo síncrono en write time (validación barrio↔ciudad, bulk geo-enrichment)
- [properties-service-users](wiki/properties-service/integrations/properties-service-users.md) — cliente hacia users-service para resolución bulk de cuentas por email→account_id, consumido por el bulk-create worker

### runbook/
- [properties-service-local-dev](wiki/properties-service/runbook/properties-service-local-dev.md) — devcontainer, env vars, create + imágenes end-to-end, 6 known gaps

### adrs/
- [ADR-0001 — Upload de imágenes vía presigned URLs + batch](wiki/properties-service/adrs/adr-image-upload-presigned-batch.md)
- [ADR-0002 — Feed orgánico + ads con fallback de preferencias](wiki/properties-service/adrs/adr-feed-ads-organic-injection.md)
- [ADR-0003 — Precio estimado dual (admin vs ML)](wiki/properties-service/adrs/adr-estimated-price-dual-signal.md)
- [ADR-0004 — H3 dual-resolution para el feed-mapa](wiki/properties-service/adrs/adr-h3-dual-resolution-map.md)
- [ADR-0005 — Cursor de paginación opaco (base64url)](wiki/properties-service/adrs/adr-feed-opaque-cursor.md)
- [ADR-0006 — Invalidación por prefijo del cache de la vitrina pública](wiki/properties-service/adrs/adr-owner-list-cache-invalidation.md)
- [ADR-0007 — Property es 1 fila = 1 listing_type, sin soporte para venta+arriendo simultáneo](wiki/properties-service/adrs/adr-single-listing-type-per-property.md)
- [ADR-0008 — Idempotencia del bulk create vía external_id determinístico](wiki/properties-service/adrs/adr-bulk-idempotent-external-id.md)
- [ADR-0009 — El listado admin pagina por offset, no con el cursor del feed](wiki/properties-service/adrs/adr-admin-offset-pagination.md)
- [ADR-0010 — La verificación es reversible y el takedown es un cambio de status](wiki/properties-service/adrs/adr-verification-reversible-lifecycle.md)
- [ADR-0011 — Las transiciones legales las sirve el backend, no las duplica el cliente](wiki/properties-service/adrs/adr-transitions-served-by-backend.md)

## users-service

- [users-service](wiki/users-service/users-service.md) — overview: identidad y perfiles, 2 dominios (`auth`/`user`), único servicio que gestiona usuarios en Keycloak, resolve bulk consumido por properties
- [users-service-architecture](wiki/users-service/users-service-architecture.md) — layout interno, 9 tablas, identidad compartida con Keycloak, worker in-process

### domain/
- [users-service-auth](wiki/users-service/domain/users-service-auth.md) — registro (saga + compensación), sesiones por cookie, reset password
- [users-service-user](wiki/users-service/domain/users-service-user.md) — perfil persona/empresa, onboarding 4 pasos, intereses, deactivación soft, resolución bulk de cuentas por email

### integrations/
- [users-service-keycloak](wiki/users-service/integrations/users-service-keycloak.md) — dos clientes (admin + auth), identidad compartida, traducción de errores
- [users-service-email-brevo](wiki/users-service/integrations/users-service-email-brevo.md) — emails transaccionales (reset, reactivación)

### workers/
- [users-service-kc-compensation](wiki/users-service/workers/users-service-kc-compensation.md) — job APScheduler que limpia usuarios Keycloak huérfanos

### runbook/
- [users-service-local-dev](wiki/users-service/runbook/users-service-local-dev.md) — devcontainer, setup de Keycloak, env vars (con trampas), 5 known gaps

### adrs/
- [ADR-0001 — Registro como saga con compensación de Keycloak](wiki/users-service/adrs/adr-keycloak-saga-compensation.md)
- [ADR-0002 — Worker de compensación in-process con APScheduler](wiki/users-service/adrs/adr-apscheduler-in-process-worker.md)
- [ADR-0003 — Action tokens de un solo uso en Redis](wiki/users-service/adrs/adr-action-tokens-redis.md)
- [ADR-0004 — Deactivación soft (Keycloak retiene el usuario)](wiki/users-service/adrs/adr-soft-deactivation.md)

## avm (workload de ML)

Par del backend, conectado a `analytics-service` vía MLflow. Vive en `data/ml/AVM/` (fuera de `backend/`) por frontera de equipos (ver `[[adr-training-separated-from-runtime]]`).

- [avm-training](wiki/avm/avm-training.md) — pipeline de training: preprocesamiento, HPO con Optuna, registro en MLflow

### adrs/
- [ADR-0001 — LightGBM con target log10 y categóricas nativas](wiki/avm/adrs/adr-lightgbm-log-target.md)
- [ADR-0002 — HPO con Optuna y reproducibilidad por seeds fijas](wiki/avm/adrs/adr-optuna-hpo-reproducibility.md)
- [ADR-0003 — Feature engineering geoespacial schema-driven](wiki/avm/adrs/adr-geospatial-feature-engineering.md)
