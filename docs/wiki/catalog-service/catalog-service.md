---
title: catalog-service
status: draft
last-verified: 2026-07-18
owners: [catalog-service]
related:
  - "[[architecture]]"
  - "[[catalog-service-architecture]]"
  - "[[catalog-service-catalog-admin]]"
  - "[[catalog-service-geo-catalog]]"
  - "[[catalog-service-poi-lifecycle]]"
sources: [../../sources/catalog-service/2026-05-21-foundational-qa.md, ../../sources/catalog-service/2026-07-18-h3-precompute-and-bulk-resolve.md]
---

## TL;DR

Microservicio responsable de **todo lo geográfico** del sistema: catálogo de países/divisiones/localidades/barrios, resolución `(lat, lon) → barrio`, y POIs (cache local sobre OpenStreetMap). **Único servicio que toca providers geo externos** (Mapbox + Overpass). Hex pattern con tres dominios (`catalog_admin`, `geo_catalog`, `geo_resolution`) sobre Postgres con PostGIS.

## Por qué existe

Tres jobs distintos:

1. **Servir el catálogo geográfico** al frontend (autocomplete con debounce: países, departamentos, ciudades, barrios) y al backend (validación de IDs).
2. **Resolver coordenadas a barrio** ([[glossary#point-in-polygon]] contra polígonos IDECA almacenados localmente). Lo consume `properties-service` al crear listing — principio `[[adr-geo-enrichment-at-write-time]]`.
3. **Mantener un cache local de POIs** para zonas que ya se georeferenciaron. Side-effect de las geo-resolutions; sirve eventualmente como feature store para el modelo AVM de [[analytics-service]] (ver Open items para la conciliación de tag set pendiente).

## Dominios

| Dominio | Estado | Qué hace |
|---|---|---|
| `catalog_admin` | implementado | CRUD + bulk uploads (CSV de barrios, GeoJSON de polígonos). Protegido con `require_admin`. |
| `geo_catalog` | implementado | Reads para frontend: countries, localities (by-country / by-admin-division / by-id), neighborhoods (by-localities / by-id). |
| `geo_resolution` | implementado | Resolución `(lat, lon) → barrio` y población lazy de POIs vía Overpass. |

`services/shared/` aloja el `CachePort` + `RedisCacheAdapter` reutilizados por los 3 dominios.

## Public surface

| Método | Path | Quién consume | Auth |
|---|---|---|---|
| GET | `/v1/health` | healthchecks | público |
| GET | `/v1/countries` | frontend (autocomplete) | público |
| GET | `/v1/localities/by-country?country_id` | frontend | público |
| GET | `/v1/localities/by-admin-division?admin_division_id` | frontend | público |
| GET | `/v1/localities/by-id?locality_id` | frontend, otros services | público |
| GET | `/v1/neighborhoods/by-localities?locality_ids` (multi) | frontend | público |
| GET | `/v1/neighborhoods/by-id?neighborhood_id` | frontend, otros services | público |
| GET | `/v1/geo-resolution/resolve-neighborhood?query&locality_id` | frontend (legacy — refactor pendiente) | público |
| GET | `/v1/geo-resolution/by-coordinates?lat&lon` | frontend / properties-service | público |
| POST | `/v1/geo-resolution/by-coordinates/bulk` | properties-service (bulk create, futuro caller) | público |
| POST | `/v1/geo-resolution/reachable-pois` | frontend (`NearbyPlaces.vue`, "Cerca del lugar") | público |
| POST/PATCH | `/v1/admin/{countries,admin-divisions,localities,neighborhoods}` | UI admin futura, scripts | `require_admin` |
| POST | `/v1/admin/localities/{id}/neighborhoods/bulk` (CSV upload) | UI admin | `require_admin` |
| POST | `/v1/admin/.../bulk/geometry` (GeoJSON FeatureCollection) | UI admin | `require_admin` |

## Consumers

- **frontend Vue**: GETs con debounce para autocomplete; futura UI admin para uploads de catálogo.
- **properties-service**: `/geo-resolution/by-coordinates` al crear listing (geo-enrichment at write time). Recibe el barrio y persiste su UUID como `barrio_ideca` del listing. `/geo-resolution/by-coordinates/bulk` (2026-07-18) existe para resolver un lote de puntos en 1-2 queries en vez de N — `BulkCreatePropertiesUseCase._enrich_location` todavía no lo consume (sigue haciendo N llamadas a `/by-coordinates`), ver Open items.
- **frontend Vue**: también consume `/geo-resolution/reachable-pois` desde `NearbyPlaces.vue` (vista de detalle de propiedad) vía `composables/pois/useReachablePois.ts` — isócronas ORS + POIs por H3 alrededor del listing.
- **analytics-service** (futuro): consumirá la tabla `points_of_interest` directamente como feature store del modelo AVM. Hoy training usa CSV de OSM manual — ver Open items.

## Refactor pendiente — `/geo-resolution/resolve-neighborhood`

El endpoint actual recibe `query: str` (address) y hace forward geocoding con Mapbox + point-in-polygon. Esto **duplica** lo que el frontend ya hace con Mapbox SDK (ver [[glossary#forward-geocoding]]).

**Estado deseado**: deprecar `resolve-neighborhood` y dejar solo `/by-coordinates` (que ya hace reverse-only). `/by-coordinates` ya es drop-in replacement funcional — dispara `BackgroundTasks.add_task(poi_uc.execute, ...)` desde 2026-06-11, y `properties-service` ya lo consume en vez de `resolve-neighborhood`. Falta el paso 3 (wrapper deprecado temporal) y el paso 4 (borrar el código Mapbox legacy) — ver [[adr-mapbox-frontend-only]] para el detalle de qué queda.

Beneficios: menos latencia, sin costo Mapbox en backend, sin cache de forward geocode, un único punto de entrada. Ver `[[adr-mapbox-frontend-only]]`.

## Boundaries — lo que catalog-service **NO** hace

- **No emite tokens** — auth la centraliza `users-service`/Keycloak. catalog solo valida.
- **No persiste listings** — `properties-service` los maneja; catalog devuelve UUID de barrio para que listings lo guarden.
- **Sí expone POIs vía endpoint** desde la implementación de `reachable-pois` (2026-06-15) — `POST /geo-resolution/reachable-pois` devuelve POIs por isócrona (`ReachablePoiItem`: nombre, categoría, lat/lon, dirección, teléfono, sitio web). `analytics-service` seguirá consumiendo la tabla `points_of_interest` por read directo a la BD para el feature store del AVM — son dos consumos distintos, no se contradicen.
- **No hace forward geocoding del lado server** (post-refactor) — el SDK de Mapbox en el SPA hace ese hop (user types address → sees point → submits lat/lon).
- **No tiene comm async** — el único side-effect async hoy es el `BackgroundTasks` del POI fetch dentro del mismo request.

## Stack

- **FastAPI + Uvicorn** — HTTP layer
- **SQLModel + Postgres + PostGIS** (imagen `postgis/postgis:17-master`) con `geoalchemy2`
- **Redis** — caché de forward geocoding + caché + lock de POI fetch zones
- **Mapbox** — forward geocoding (legacy en `resolve-neighborhood`)
- **Overpass API** — POIs desde OpenStreetMap por bbox
- **OpenRouteService (ORS)**, self-hosted — isócronas para `reachable-pois` (ver [[adr-isochrone-ors-h3]])
- **h3** — indexación espacial (resolución 9, ~300 m)
- **PyJWT + cryptography** — validación de JWT contra JWKS de Keycloak

## Roadmap inmediato

- [ ] Refactor `/geo-resolution`: deprecar `resolve-neighborhood` (BackgroundTasks ya en `by-coordinates` ✅)
- [ ] Side-container de seed con CSVs IDECA al startup (hoy es bulk manual)
- [x] Conciliar tag set Overpass con tag set del training del AVM — `category_map.py` (2026-06-11)
- [ ] FetchZone refresh batch (cron / worker) para zonas stale
- [ ] UI admin frontend para uploads de catálogo
- [x] Implementar `ReachablePoiUseCase` — isócronas ORS + H3, wired a `POST /geo-resolution/reachable-pois` y consumido por `NearbyPlaces.vue` en el frontend (ver [[adr-isochrone-ors-h3]])

## Related

- [[architecture]] — monorepo, hex pattern, patrones de comunicación
- [[catalog-service-architecture]] — arquitectura interna
- [[catalog-service-catalog-admin]] — dominio writes
- [[catalog-service-geo-catalog]] — dominio reads
- [[catalog-service-poi-lifecycle]] — POI cache-aside + FetchZone + H3 lazy-fill
- [[catalog-service-local-dev]] — runbook
- [[adr-geo-enrichment-at-write-time]] — principio cross-service que respalda el reverse geocoding

## Claims

- `catalog-service` define 3 dominios bajo `src/app/services/`: `catalog_admin`, `geo_catalog`, `geo_resolution` ([services/](backend/catalog-service/src/app/services)).
- El router incluye 6 sub-routers: `health`, `countries`, `localities`, `neighborhoods`, `geo_resolution`, `admin` ([api/main.py:3-10](backend/catalog-service/src/app/api/main.py#L3-L10)).
- Las rutas `/admin/*` están protegidas globalmente vía `Depends(require_admin)` en el `APIRouter` ([api/routes/admin.py:74](backend/catalog-service/src/app/api/routes/admin.py#L74)).
- `require_admin` chequea `settings.ADMIN_ROLE in principal.roles` con `roles` extraídos de `realm_access.roles` del JWT ([api/deps/auth.py:99-104](backend/catalog-service/src/app/api/deps/auth.py#L99-L104)).
- `/geo-resolution/resolve-neighborhood` dispara la población de POIs vía `BackgroundTasks.add_task(poi_uc.execute, ...)` fire-and-forget ([api/routes/geo_resolution.py:32-38](backend/catalog-service/src/app/api/routes/geo_resolution.py#L32-L38)).
- `/geo-resolution/by-coordinates` dispara el background task de POIs desde 2026-06-11 ([api/routes/geo_resolution.py](backend/catalog-service/src/app/api/routes/geo_resolution.py#L43-L59)).
- catalog-service y properties-service usan la imagen `postgis/postgis:17-master` en el `docker-compose.yml`; los Postgres de users-service y keycloak son `postgres:17` plano.
- 6 routers, 22 endpoints en total al 2026-07-18 (contados directo de los decoradores `@router.get/post/patch` en `src/app/api/routes/*.py`: admin 11, countries 1, geo_resolution 4, health 1, localities 3, neighborhoods 2).
- `POST /geo-resolution/by-coordinates/bulk` (agregado 2026-07-18) resuelve un lote de `{id, lat, lon}` en una sola respuesta, vía `BulkResolveLocationsByCoordinatesUseCase` + `get_location_by_points` (unnest + LATERAL JOIN) ([api/routes/geo_resolution.py](backend/catalog-service/src/app/api/routes/geo_resolution.py)).
- `POST /geo-resolution/reachable-pois` está implementado y wireado end-to-end: `services/geo_resolution/use_cases/resolve_isochrone.py` + integración ORS en `integrations/georef/ors/routing.py` ([api/routes/geo_resolution.py:67-72](backend/catalog-service/src/app/api/routes/geo_resolution.py#L67-L72)).
