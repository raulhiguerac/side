---
title: Project roadmap — estado y visión 2026
captured-from: conversation
captured-on: 2026-05-29
participants: [raul, claude]
---

## Context
El autor dictó el estado actual del roadmap + nuevos items (notifications-ms, payments-ms, heatmap desde DWH, K3s/Minikube con NetworkPolicies).

## Completado

### Fase 1 — Catálogo + Onboarding
- catalog-ms MVP: CRUD geo completo (Country/AdminDivision/Locality/Neighborhood/POI), geo-resolution, cache Redis, PostGIS, 91 unit tests
- users-ms: registro + sesión Keycloak, onboarding 4 pasos, intereses, soft-deactivation
- Frontend: landing page, onboarding modal wizard, locality selector conectado al catálogo

### Fase 2 — Properties (mayormente completo)
- properties-service: modelos (5 tablas PostGIS+H3), listing UCs, image UCs (presigned batch), search feed UC, DI wiring, routers, seed_mapper
- Pendiente en Fase 2: Alembic migrations finales, bulk_create, SqlAdminPropertyRepository.bulk_insert

### Fase 3 — AVM / Analytics
- ML pipeline: LightGBM + Optuna HPO, bogota-avm @production v1 en MLflow (MinIO artifact store)
- analytics-ms: prediction domain completo (ports/adapters/UC/error), wiring DI + router + Alembic migrations, /predict endpoint online
- Frontend AVM: form multi-step (GMaps Places autocomplete → neighborhood resolution → submit), mapa reactivo con marker en tiempo real, cableo end-to-end con /predict

## En progreso / pendiente

### Fase 4 — Seed + Infra básica
- Properties seed Bogotá (bulk import desde dataset IDECA/fuentes abiertas)
- CI/CD pipeline básico

## Nuevos items (por fase)

### Analytics — Heatmap desde DWH
- Mapa de calor de precios por zona geográfica
- Requiere DWH (data warehouse) como fuente — no sirve la DB OLTP del analytics-ms para queries analíticos pesados
- Stack no decidido: BigQuery, DuckDB, o Redshift según costos

### Nuevos microservicios (draft)
- **notifications-ms**: notificaciones push/email para matching propiedades, cambios de precio, alertas de barrio. Stack a definir (Firebase FCM + Brevo o similar)
- **payments-ms**: pagos para monetización (suscripciones premium, destacar listings). Stack a definir (Stripe o PSE local)

### Infraestructura — K3s / Minikube
- Reemplazar docker-compose por orquestación real (K3s para prod ligero, Minikube para dev local)
- NetworkPolicies para aislar las DBs: solo el MS dueño puede acceder a su Postgres/Redis
- Objetivo: cada MS en su propio namespace con egress restringido hacia otras DBs

## Open questions
- DWH para heatmap: ¿managed (BigQuery) o self-hosted (DuckDB sobre MinIO)?
- notifications-ms: ¿mismo Keycloak para auth o token propio?
- payments-ms: ¿Stripe (USD) o PSE/wompi (COP local)?
- K3s vs Minikube: K3s si se despliega en VPS/cloud, Minikube solo para dev local
