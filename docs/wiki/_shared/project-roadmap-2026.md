---
title: Project roadmap 2026
status: stable
last-verified: 2026-07-29
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[open-items]]"
  - "[[deployment-k8s-helm]]"
  - "[[analytics-service]]"
  - "[[properties-service]]"
  - "[[frontend]]"
  - "[[avm-training]]"
sources: [../../sources/_shared/2026-05-29-project-roadmap.md, ../../sources/_shared/2026-05-31-impressions-feed-personalization-supply.md, ../../sources/properties-service/2026-06-08-feed-cache-geo-scaling.md, ../../sources/_shared/2026-06-09-mvp-audit-scores.md, ../../sources/_shared/2026-07-29-k8s-helm-microservice-chart.md]
---

## TL;DR

Monorepo `side` — plataforma inmobiliaria colombiana. Backend hexagonal (Python/FastAPI), frontend Vue 3, ML con LightGBM + MLflow. Roadmap en 4 fases: catálogo ✅ → propiedades 🔄 → AVM online ✅ → forms básicos → infra → diferenciadores.

> Para el detalle accionable de cada ítem (bugs, deuda, gaps de mercado) ver [[open-items]] — los ítems están etiquetados por fase para que ambos documentos hablen entre sí.

## Fase 1 — Catálogo + Onboarding ✅

| Item | Estado |
|---|---|
| catalog-ms MVP (CRUD geo, geo-resolution, POIs, Redis, PostGIS) | ✅ |
| users-ms (registro Keycloak, sesión cookie, onboarding 4 pasos, intereses) | ✅ |
| Frontend landing + modal onboarding + locality selector | ✅ |

## Fase 2 — Properties 🔄

| Item | Estado |
|---|---|
| Modelos (5 tablas PostGIS + H3), listing UCs, image UCs presigned batch | ✅ |
| Search feed UC, DI wiring, routers, seed_mapper | ✅ |
| Cursor pagination opaco (base64url) + Redis cache-aside en feed | ✅ |
| `PropertiesView` parent + toggle Lista/Mapa (nested routes `/feed/list`, `/feed/map`) | ✅ |
| bulk_create UC, SqlAdminPropertyRepository.bulk_insert | ✅ |
| Properties seed Bogotá (bulk import IDECA) | ✅ |
| Frontend: vista detalle de propiedad (`/listing/:id`) — galería, info completa, mapa ✅; precio estimado ⏳ | 🔄 |
| Frontend: form publicar propiedad + subir imágenes + gestionar mis listings (`/properties`) | ✅ |
| Frontend: MapView con Leaflet + bbox + paginación de resultados | ✅ |
| Frontend: panel de moderación admin — aprobar/rechazar listings que infringen políticas | ⏳ |

Ver [[properties-service]], [[properties-service-listing]], [[properties-service-search]].

## Fase 3 — AVM / Analytics ✅

| Item | Estado |
|---|---|
| ML pipeline: LightGBM + Optuna HPO, bogota-avm @production v1 en MLflow | ✅ |
| analytics-ms: prediction domain, wiring DI, Alembic, /predict endpoint | ✅ |
| analytics-ms: Kafka worker (`runner.py`) no se levanta en `main.py` startup — batch pipeline off by default | ⏳ |
| Frontend AVM: form multi-step, GMaps Places, mapa reactivo, cableo /predict | ✅ |
| Re-registrar modelo con `year_built` nullable en MLflow schema | ⏳ |

Ver [[analytics-service]], [[avm-training]], [[analytics-service-mlflow]], [[frontend-architecture]].

## Fase 4 — Infra 🔄

Prioridad: forms básicos de Fase 2 primero, luego infra, luego diferenciadores. **Arrancada 2026-07-29** en modo aprendizaje — detalle completo en [[deployment-k8s-helm]].

### Infraestructura — Helm + kind → GKE
- **Enfoque decidido**: chart Helm genérico por microservicio (`k8s/charts/microservice/`), reusable para los 4 vía `values/<ms>.yaml`. Se pivotó de Kustomize a Helm.
- **Self-host** de lo stateful (Postgres vía CloudNativePG, Redis, MinIO, Kafka como pods) — no managed GCP.
- **Cluster**: kind local primero, GKE después. Deploy **diferido**: el PC actual no corre kind ni helm; hoy solo autoría del chart.
- **NetworkPolicies**: cada MS en su namespace con egress restringido — requiere CNI Calico/Cilium (kindnet no las aplica). Ver [[open-items]].
- **Secretos**: dummy tras flag en dev; reales por Sealed Secrets/ESO (fase de seguridad).
- Objetivo: blast radius mínimo. Portable a GKE sin reescribir el chart.

### CI/CD
- Pipeline: lint → test → build → push → deploy.
- GitHub Actions. Backup etcd para disaster recovery.

## Fase 5 — Diferenciadores ⏳

### Score de oportunidad de inversión (alta prioridad)
- `(precio_listado - ml_estimated_price) / ml_estimated_price` inline en cada card del feed.
- Diferenciador directo vs FincaRaíz/Metrocuadrado. Requiere worker Kafka properties↔analytics funcionando.
- Ver [[adr-estimated-price-dual-signal]], [[open-items]].

### Isócronas (geo diferenciador)
- `GET /v1/geo-resolution/reachable-pois`: dado lat/lon + minutos + modo → ORS routing → polígono → H3 cells → POIs en el área.
- Motor de routing: OpenRouteService (self-hosted o tier gratis). Mapbox descartado por cobertura en Colombia.
- Renderizado: capa GeoJSON en Leaflet sobre el MapView.
- Ver [[catalog-service-poi-lifecycle]], [[open-items]].

### Impresiones y personalización del feed
- Evento Kafka `listing.impressed` → analytics-ms → recomendador colaborativo/content-based.
- Dashboard de impresiones para el propietario (alcance de su listing).
- Feed evoluciona: preferencias declaradas → comportamiento (views, tiempo, retorno) → ranking personalizado.
- El bbox del mapa es señal implícita de zona de interés sin acción explícita.
- Ver [[adr-impressions-beacon-pipeline]], [[open-items]].

### LLM con tool use para búsqueda en lenguaje natural
- Traducir query libre → `FeedPreferences + FeedFilters` vía tool use.
- Ejemplo: "apartamento 2 hab en Chapinero por menos de 500M" → payload tipado al endpoint existente.
- El endpoint ya soporta todos los parámetros — falta solo la capa de traducción.
- Cerouno ya la tiene → brecha competitiva activa.

### Alertas de oportunidad de precio
- Notificación push/email cuando se lista una propiedad X% por debajo del estimado en la zona de interés del usuario.
- Requiere: AVM funcionando + notifications-ms + preferencias de zona (onboarding).

### Analytics — Heatmap desde DWH
- Mapa de calor de precios por zona geográfica.
- La DB OLTP del analytics-ms no es apta para queries analíticos pesados → DWH separado.
- Stack a decidir: BigQuery (managed) vs DuckDB sobre MinIO (self-hosted).

### notifications-ms (draft)
- Notificaciones push/email: matching de propiedades, cambios de precio, alertas de barrio.
- Stack a definir: Firebase FCM + Brevo. Auth: reusar Keycloak.

### payments-ms (draft)
- Monetización: suscripciones premium, destacar listings.
- Stack a definir: Stripe (USD) vs Wompi/PSE (COP, mercado local).

## Open questions

- [ ] DWH para heatmap: ¿BigQuery managed o DuckDB self-hosted sobre MinIO?
- [ ] notifications-ms: ¿mismo Keycloak o token propio para push?
- [ ] payments-ms: ¿Stripe o Wompi/PSE como PSP primario?
- [ ] Infra: self-host de lo stateful sobre Kubernetes (kind local hacia GKE, chart Helm generico) decidido 2026-07-29 (ver [[deployment-k8s-helm]]); managed vs self-host para la prod definitiva sigue abierto
- [ ] Supply inicial: ¿listings de venta, arriendo, o ambos?

## Claims

- El endpoint `POST /v1/predict` del analytics-ms está operativo y cableado desde el frontend AVM al 2026-05-29 ([routes/predict.py](backend/analytics-service/src/app/api/routes/predict.py)).
- El feed pagina por cursor opaco con Redis cache-aside (TTL 5 min, solo orgánicos) al 2026-06-08 ([get_feed.py](backend/properties-service/src/app/services/search/use_cases/get_feed.py)).
- `PropertiesView` con toggle Lista/Mapa en nested routes `/feed/list` y `/feed/map` operativo al 2026-06-08 ([router/index.ts](frontend/src/router/index.ts)).
- notifications-ms y payments-ms están en fase draft — no hay código en el repo al 2026-06-08.
- La estrategia de despliegue objetivo es un chart Helm generico por microservicio en `k8s/charts/microservice/` sobre kind local hacia GKE, con self-host de lo stateful (Postgres via CloudNativePG) — docker-compose es solo para desarrollo local.
