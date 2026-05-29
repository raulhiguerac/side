---
title: properties-service — exploración foundational del código
captured-from: conversation
captured-on: 2026-05-28
participants: [raul, claude]
---

## Context

Primera documentación de `properties-service` en la wiki. Se exploró el código del servicio a fondo para producir las páginas wiki (overview, arquitectura, dominios, integraciones, runbook, ADRs). Este source registra los hallazgos no triviales que no se ven de un solo archivo.

## Key conclusions

- **Tres dominios** bajo `services/`: `listing` (CRUD del dueño + imágenes), `search` (feed público + mapa), `admin` (moderación, precios estimados, promociones, bulk). `shared/` aloja ports/adapters/schemas comunes (catalog gateway, cache, storage, property cards).
- **Hex pattern idéntico al resto del backend**: UCs → ports → adapters; DI con FastAPI `Depends`. Adapters stateless (`CacheClient`, `CatalogClient`, `StorageClient`) cacheados con `@lru_cache(maxsize=1)`; UoW request-scoped sobre `Session`.
- **5 tablas** en una sola migración: `properties`, `property_locations` (PostGIS POINT), `property_images`, `property_image_upload_batches`, `promoted_listings`.
- **Auth por cookie** `access_token` (no header Bearer) — igual que catalog-service, distinto de analytics. `require_admin` chequea `ADMIN_ROLE` en `realm_access.roles`.
- **Geo-enrichment at write time**: `create_property` llama sincrónicamente a catalog `/v1/neighborhoods/by-id` para validar que el barrio pertenece a la ciudad, y computa `h3_r9`/`h3_r7` localmente. Principio `[[adr-geo-enrichment-at-write-time]]`.
- **Imágenes vía presigned URLs + batch**: el cliente pide URLs presignadas (crea un `PropertyImageUploadBatch` con `expected_keys` y TTL), sube directo a MinIO, y confirma. Confirm valida estado/expiración/subconjunto de keys e inserta los `PropertyImage`.
- **Feed = ads + organic**: `get_ads` (promociones, cache por ciudad o global, TTL 1h) intercalado en resultados organicos cada `FEED_AD_INTERVAL`. Organic usa **fallback por fases** de preferencias (barrio+ciudad+tipo → ciudad+tipo → todo) y paginación por cursor `(created_at, id, position)`.
- **Feed mapa**: bbox → celdas H3 → cache-aside por celda (`map:h3:<index>`), miss va a Postgres por `get_by_bbox`. Resolución 9 (~300m) o 7 (~5km) según zoom.
- **Precio estimado dual**: `admin_estimated_price` y `ml_estimated_price` se guardan **por separado** para preservar ambas señales para training del AVM. El mismo UC `SetEstimatedPriceUseCase` decide cuál escribir según haya `principal` (admin) o no (ML).
- **Sin worker Kafka**: `workers/` está vacío (solo `__init__.py`). El path ML de `set_estimated_price` (principal=None) **no tiene caller aún** — está listo para un futuro consumer de `price-predicted` de [[analytics-service]], pero hoy no existe.
- **Bulk create** replica el patrón de analytics: `bulk_insert` con fallback row-by-row vía `begin_nested()`/`rollback_to_savepoint()`, más geo-enrichment concurrente (Semaphore de 50) contra catalog `/by-coordinates`.
- **State machine de status** en `set_status`: transiciones permitidas explícitas (`draft↔active`, `active→{inactive,sold,rented}`, etc.). Cache se invalida por property, por owner y por celdas H3.
- **Cache-aside con visibilidad**: `get_property` solo cachea propiedades `active`; las no-active solo las ve el owner.

## Open questions

- ¿Cuándo se agrega el worker que consume `price-predicted` y llama `set_estimated_price` con principal=None? Hoy el path ML está huérfano.
- `.env.example` del servicio está incompleto (solo `DATABASE_URL` y `REDIS_URL`) — faltan Keycloak, storage (MinIO), `CATALOG_URL`, TTLs.

## Next steps

- Documentar properties-service en la wiki (hecho en esta sesión).
- Considerar un ADR cross-service para el contrato `price-predicted` cuando se implemente el worker.
