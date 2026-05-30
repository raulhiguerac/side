---
title: Project roadmap 2026
status: draft
last-verified: 2026-05-29
owners: [_shared]
related: [[architecture]], [[open-items]], [[analytics-service]], [[properties-service]], [[frontend]], [[avm-training]]
sources: [../../sources/_shared/2026-05-29-project-roadmap.md]
---

## TL;DR

Monorepo `side` — plataforma inmobiliaria colombiana. Backend hexagonal (Python/FastAPI), frontend Vue 3, ML con LightGBM + MLflow. Roadmap en 4 fases: catálogo ✅ → propiedades 🔄 → AVM online ✅ → seed + infra + nuevos MS.

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
| Alembic migrations finales, bulk_create, SqlAdminPropertyRepository.bulk_insert | ⏳ |
| Properties seed Bogotá (bulk import IDECA) | ⏳ |

Ver [[properties-service]], [[properties-service-listing]], [[properties-service-search]].

## Fase 3 — AVM / Analytics ✅

| Item | Estado |
|---|---|
| ML pipeline: LightGBM + Optuna HPO, bogota-avm @production v1 en MLflow | ✅ |
| analytics-ms: prediction domain, wiring DI, Alembic, /predict endpoint | ✅ |
| Frontend AVM: form multi-step, GMaps Places, mapa reactivo, cableo /predict | ✅ |
| Re-registrar modelo con `year_built` nullable en MLflow schema | ⏳ |

Ver [[analytics-service]], [[avm-training]], [[analytics-service-mlflow]], [[frontend-architecture]].

## Fase 4 — Infra + Nuevos MS ⏳

### CI/CD
- Pipeline básico (GitHub Actions o similar): lint → test → build → deploy.

### Infraestructura — K3s / Minikube
- Reemplazar docker-compose por orquestación real: **K3s** para VPS/cloud ligero, **Minikube** para dev local.
- **NetworkPolicies**: cada MS en su propio namespace con egress restringido — solo el MS dueño puede alcanzar su Postgres/Redis. Las DBs no son alcanzables entre namespaces.
- Objetivo: blast radius mínimo si un MS se ve comprometido.

### Analytics — Heatmap desde DWH
- Mapa de calor de precios por zona geográfica sobre el feed.
- La DB OLTP del analytics-ms no es apta para queries analíticos pesados → requiere DWH separado.
- Stack a decidir: BigQuery (managed, pay-per-query) vs DuckDB sobre MinIO (self-hosted, sin egress cost).

### notifications-ms (draft)
- Notificaciones push/email: matching de propiedades, cambios de precio, alertas de barrio.
- Stack a definir: Firebase FCM + Brevo o similar. Auth: reusar Keycloak.

### payments-ms (draft)
- Monetización: suscripciones premium, destacar listings.
- Stack a definir: Stripe (USD, tarjeta internacional) vs Wompi/PSE (COP, mercado local).

## Open questions

- [ ] DWH para heatmap: ¿BigQuery managed o DuckDB self-hosted sobre MinIO?
- [ ] notifications-ms: ¿mismo Keycloak o token propio para push?
- [ ] payments-ms: ¿Stripe o Wompi/PSE como PSP primario?
- [ ] K3s en VPS o cloud managed (GKE/EKS) para producción?

## Claims

- El endpoint `POST /v1/predict` del analytics-ms está operativo y cableado desde el frontend AVM al 2026-05-29 ([routes/predict.py](backend/analytics-service/src/app/api/routes/predict.py)).
- notifications-ms y payments-ms están en fase de draft — no hay código en el repo al 2026-05-29.
- El heatmap de precios requiere DWH separado — la DB OLTP del analytics-ms no es apta para queries analíticos de agregación masiva.
- La estrategia de despliegue objetivo es K3s/Minikube con NetworkPolicies por namespace — docker-compose es solo para desarrollo local.
