---
title: properties-service
status: draft
last-verified: 2026-07-13
owners: [properties-service]
related:
  - "[[architecture]]"
  - "[[properties-service-architecture]]"
  - "[[properties-service-listing]]"
  - "[[properties-service-search]]"
  - "[[properties-service-admin]]"
sources: [../../sources/properties-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

Microservicio **core del producto**: dueño de los listings inmobiliarios (CRUD, imágenes, visibilidad), del **feed público** (búsqueda + mapa) y del **panel admin** (moderación, promociones, precios estimados, bulk). Hex pattern con tres dominios (`listing`, `search`, `admin`) sobre Postgres con PostGIS. Síncrono/HTTP — **sin worker Kafka hoy**. Depende de [[catalog-service]] para validar geografía al crear listings.

## Por qué existe

Es el agregado central del dominio inmobiliario. Tres responsabilidades:

1. **Listings del dueño** — un usuario autenticado crea/edita/borra sus propiedades y administra sus fotos (upload directo a object storage vía URLs presignadas).
2. **Descubrimiento público** — el feed paginado (mezcla orgánico + promociones) y el feed-mapa por viewport que consume el frontend.
3. **Operación interna** — moderación (status + verificación), promociones pagas, y precios estimados (manual del admin y/o del modelo AVM).

## Dominios

| Dominio | Estado | Qué hace |
|---|---|---|
| `listing` | implementado | CRUD de propiedades del owner, visibilidad, y flujo de imágenes (presigned + confirm + delete). |
| `search` | implementado | Feed público (orgánico + ads) y feed-mapa por bounding box con H3. Sin auth. |
| `admin` | implementado | Moderación (status/verificación), precios estimados (admin/ML), promociones, bulk create. Protegido con `require_admin`. |

`services/shared/` aloja los ports + adapters reutilizados por los 3 dominios: `CatalogGateway`, `CachePort`, `StoragePort`, y los schemas `PropertyCardSchema` / `PropertyDetailSchema`.

## Public surface

| Método | Path | Quién consume | Auth |
|---|---|---|---|
| GET | `/properties/me` | frontend (mis propiedades) | cookie |
| GET | `/properties/users/{user_id}` | frontend (perfil público) | público |
| POST | `/properties` | frontend (crear) | cookie |
| GET | `/properties/{property_id}` | frontend (detalle) | cookie opcional |
| PATCH | `/properties/{property_id}` | frontend (editar) | cookie |
| DELETE | `/properties/{property_id}` | frontend | cookie |
| POST | `/properties/{property_id}/visibility` | frontend | cookie |
| POST | `/properties/images/presigned-urls` | frontend (pedir URLs de subida) | cookie |
| POST | `/properties/{property_id}/images/confirm` | frontend (confirmar subida) | cookie |
| DELETE | `/properties/{property_id}/images` | frontend | cookie |
| GET | `/search/feed` | frontend (feed) | público |
| GET | `/search/feed/map` | frontend (mapa) | público |
| POST/GET/PATCH | `/admin/properties...` | UI admin | `require_admin` |
| POST/GET/DELETE | `/admin/promotions...` | UI admin | `require_admin` |

## Consumers

- **frontend Vue**: feed, mapa, CRUD del dueño, upload de fotos, UI admin.
- **[[catalog-service]]** (saliente): properties llama a catalog en write time — `/v1/neighborhoods/by-id` para validar barrio↔ciudad al crear, `/v1/geo-resolution/by-coordinates` en el bulk para enriquecer lat/lon → IDs geográficos.
- **[[analytics-service]]** (futuro): el modelo AVM escribirá `ml_estimated_price` vía un worker pendiente que consumiría el topic `price-predicted`. Hoy ese path no tiene caller.

## Boundaries — lo que properties-service **NO** hace

- **No emite tokens** — auth la centraliza Keycloak ([[users-service]]); properties solo valida el JWT de la cookie.
- **No resuelve geografía** — delega en [[catalog-service]]. Solo computa los índices H3 localmente a partir de lat/lon ya validadas.
- **No genera predicciones de precio** — eso es de [[analytics-service]]; properties solo persiste el resultado en `ml_estimated_price`.
- **No tiene comm async hoy** — `workers/` está vacío. Todo es HTTP síncrono.
- **No procesa imágenes** — el cliente sube directo a MinIO con URLs presignadas; properties solo registra metadata y URLs públicas.

## Stack

- **FastAPI + Uvicorn** — HTTP layer
- **SQLModel + Postgres + PostGIS** (imagen `postgis/postgis:17-master`) con `geoalchemy2` + `shapely`
- **Redis** — cache de detalle, mis-propiedades, ads del feed, celdas del mapa, batch de imágenes
- **MinIO / S3** (`boto3`) — fotos de propiedades vía URLs presignadas
- **h3** — indexación espacial dual (r9 ~300m detalle, r7 ~5km mapa)
- **PyJWT** — validación de JWT contra JWKS de Keycloak

## Roadmap inmediato

- [ ] Worker que consuma `price-predicted` de analytics y llame `set_estimated_price` (path ML hoy huérfano)
- [ ] Completar `.env.example` (Keycloak, MinIO, `CATALOG_URL`, TTLs)
- [ ] Materializar la migración en CI/seed reproducible

## Related

- [[architecture]] — monorepo, hex pattern, patrones de comunicación
- [[properties-service-architecture]] — arquitectura interna
- [[properties-service-listing]] — dominio del dueño + imágenes
- [[properties-service-search]] — feed público + mapa
- [[properties-service-admin]] — moderación, promociones, precios
- [[properties-service-catalog]] — integración geo síncrona
- [[properties-service-local-dev]] — runbook
- [[adr-geo-enrichment-at-write-time]] — principio cross-service del enriquecimiento geo

## Claims

- `properties-service` define 3 dominios bajo `services/`: `listing`, `search`, `admin`, más `shared` ([services/](backend/properties-service/src/app/services)).
- El `api_router` incluye 4 routers: `health`, `properties`, `search`, `admin` ([api/main.py:7-10](backend/properties-service/src/app/api/main.py#L7-L10)).
- Las rutas `/admin/*` están protegidas globalmente vía `dependencies=[Depends(require_admin)]` en el `APIRouter` ([api/routes/admin.py:43-47](backend/properties-service/src/app/api/routes/admin.py#L43-L47)).
- Auth lee el JWT desde la cookie `access_token`, no del header `Authorization` ([api/deps/auth.py:46](backend/properties-service/src/app/api/deps/auth.py#L46)).
- `workers/` solo contiene `__init__.py` — no hay consumer Kafka al 2026-05-28 ([workers/](backend/properties-service/src/app/workers)).
- `create_property` valida contra catalog que el barrio pertenece a la ciudad antes de persistir ([create_property.py:25-31](backend/properties-service/src/app/services/listing/use_cases/property_core/create_property.py#L25-L31)).
- El servicio usa la imagen `postgis/postgis:17-master` para su DB `properties-ms-db` ([docker-compose.yml:41-42](docker-compose.yml#L41-L42)).
