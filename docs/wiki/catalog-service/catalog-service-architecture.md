---
title: Arquitectura interna de catalog-service
status: draft
last-verified: 2026-05-21
owners: [catalog-service]
related:
  - "[[architecture]]"
  - "[[catalog-service]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[adr-postgis-h3-hybrid]]"
  - "[[adr-poi-cache-aside]]"
sources: [../../sources/catalog-service/2026-05-21-foundational-qa.md]
---

## TL;DR

Hex pattern estándar del backend con **3 dominios activos** (vs el mono-dominio de [[analytics-service]]): `catalog_admin` (writes admin), `geo_catalog` (reads frontend), `geo_resolution` (providers + reverse geocoding). Cache layer compartido (`CachePort` + `RedisCacheAdapter`) en `services/shared/`. Postgres con [[glossary#postgis]] para spatial. Auth via **cookie** `access_token` JWT validado contra JWKS de Keycloak (patrón distinto al de analytics, que usa header).

## Layout

```
src/app/
├── api/
│   ├── deps/
│   │   ├── auth.py             # get_current_principal, require_admin, jwks_client global
│   │   ├── db.py
│   │   ├── catalog_admin.py    # DI factories para los UCs de catalog_admin
│   │   ├── geo_catalog.py      # DI factories para los UCs de geo_catalog
│   │   ├── geo_resolution.py   # DI factories para los UCs de geo_resolution
│   │   └── upload_validation.py
│   ├── handlers/
│   │   └── exception_handlers.py
│   ├── middleware/
│   │   └── correlation_id.py
│   └── routes/
│       ├── health.py
│       ├── countries.py
│       ├── localities.py
│       ├── neighborhoods.py
│       ├── geo_resolution.py
│       └── admin.py
├── core/
│   ├── config/settings.py      # DB, Redis, Keycloak, cache TTLs, h3 res, Overpass timeout
│   ├── exceptions/             # base, cache, catalog_admin, geo_catalog, geo_resolution, validation
│   ├── files/                  # policies, validators (upload constraints)
│   └── logging/
├── db/
├── integrations/
│   ├── cache/redis/cache.py    # CacheClient (lib infra)
│   ├── georef/
│   │   ├── mapbox/             # GeoreferentiationClient (forward geocode)
│   │   └── pois/overpass.py    # PoiClient (bbox → POIs categorized)
│   └── storage/minio/          # scaffolded, no uso runtime
├── models/
│   └── location.py             # Country, AdminDivision, Locality, Neighborhood, POI, FetchZone
├── schemas/                    # principal, base DTOs
├── services/
│   ├── catalog_admin/          # writes + bulk uploads
│   ├── geo_catalog/            # reads frontend
│   ├── geo_resolution/         # reverse + POI population
│   └── shared/                 # CachePort + RedisCacheAdapter + helpers
└── main.py                     # FastAPI factory (incluye CORS allow_origins=*)
```

Reglas comunes ya documentadas en [[architecture]] — hex pattern, ports como `typing.Protocol`, adapters wire DI vía `api/deps/`.

## Dominio `catalog_admin`

Writes al catálogo. UCs por entidad + bulk uploads:

| Pieza | Archivos |
|---|---|
| UCs CRUD | `create_country`, `update_country`, `create_admin_division`, `update_admin_division`, `create_locality`, `update_locality`, `create_neighborhood`, `update_neighborhood` |
| UCs bulk | `bulk_create_neighborhoods` (CSV), `bulk_enrich_neighborhood_geometries` (GeoJSON FeatureCollection), `enrich_neighborhood_geometry` (single GeoJSON) |
| Ports | `country_repository`, `admin_division_repository`, `locality_repository`, `neighborhood_repository`, `unit_of_work` |
| Adapters SQL | `sql_country_repository`, `sql_admin_division_repository`, `sql_locality_repository`, `sql_neighborhood_repository`, `sql_unit_of_work` |
| Helpers | `file_parser.NeighborhoodFileParser` (parsea CSV), `db_error_translator` (mapea errores SQL a errores de dominio) |

Ver [[catalog-service-catalog-admin]] para detalle.

## Dominio `geo_catalog`

Reads para frontend / consumers read-only:

| UC | Endpoint |
|---|---|
| `GetCountriesUseCase` | `GET /countries` |
| `GetLocalitiesUseCase` | `GET /localities/by-country`, `/by-admin-division` |
| `GetLocalityByIdUseCase` | `GET /localities/by-id` |
| `GetNeighborhoodsByLocalityUseCase` | `GET /neighborhoods/by-localities` (acepta múltiples `locality_ids`) |
| `GetNeighborhoodByIdUseCase` | `GET /neighborhoods/by-id` |

Ports y adapters separados de `catalog_admin` (distintos repos read-optimized). Helpers: `cache_keys.py` con constructores de keys de Redis. Ver [[catalog-service-geo-catalog]].

## Dominio `geo_resolution`

El más interesante. Tres UCs.

### `ResolveNeighborhoodUseCase` (legacy — refactor pendiente)
Endpoint `/geo-resolution/resolve-neighborhood?query&locality_id`. Flujo:

1. **Forward geocode con cache**: intenta Redis (key `cache_key_forward_geocode(query, locality_id)`); si miss, lookup `country_code` + `proximity` de la locality en DB, llama Mapbox vía `GeocodingGateway.forward_geocode`, persiste el `(lat, lon)` resultado con TTL `CACHE_TTL_ENTITY_SECONDS` (30 días).
2. **Reverse**: `uow.georef.get_neighborhood_by_coordinates(lat, lon, locality_id)` — PostGIS point-in-polygon contra los barrios de la locality.
3. Returns `ResolvedNeighborhood`.
4. El endpoint inyecta también `ResolvePoiUseCase` y dispara `BackgroundTasks.add_task(poi_uc.execute, ...)` fire-and-forget para poblar POIs de la zona.

### `ResolveLocationByCoordinatesUseCase` (el reverse-only canónico)
Endpoint `/geo-resolution/by-coordinates?lat&lon`. Flujo simple:

1. `uow.georef.get_location_by_point(lat, lon)` → `LocationByCoordinates`.

Hoy **no dispara** el POI background task. Es el destino del refactor pendiente (ver [[catalog-service]] roadmap).

### `ResolvePoiUseCase` (side-effect fire-and-forget)
Nunca se invoca directo desde HTTP — solo como background task del UC de arriba. Detalle completo en [[catalog-service-poi-lifecycle]]. Resumen:

- 3 capas de dedup: Redis cache short-circuit → Redis lock (`set_nx`) → DB `FetchZone` freshness check.
- Al fetchear: `bbox = h3.cell_to_boundary` → Overpass → persiste POIs → registra `FetchZone` → **appendea el `h3_index` al array `h3_cells` del neighborhood** (esa es la lazy-fill mechanism, ver [[glossary#h3]]).

## Capa de integración

### Mapbox ([integrations/georef/mapbox/georeferentiation.py](backend/catalog-service/src/app/integrations/georef/mapbox/georeferentiation.py))
`GeoreferentiationClient`. Wrappea SDK Python `mapbox`. Solo `forward_geocoding(address, country_code, proximity)` implementado. Requiere env `MAPBOX_API_KEY`. Maneja `ValidationError`, `ConnectionError`, `Timeout`, `HTTPError` → mapea a 4 errores de dominio (`GeoResolutionMisconfiguredError`, `GeoResolutionBadRequestError`, `GeoResolutionUnavailableError`, `GeoResolutionNotFoundError`).

El adapter `geo_resolution/adapters/geocoding.py` traduce entre el GeoJSON crudo y un `GeocodingResult` (lat, lon, formatted_address).

### Overpass ([integrations/georef/pois/overpass.py](backend/catalog-service/src/app/integrations/georef/pois/overpass.py))
`PoiClient`. Wrappea lib `overpass`. Solo `get_pois_by_bbox(bbox)` implementado. Query Overpass QL hardcodeada con tag set fijo: ~15 tags entre `amenity` (restaurant, school, hospital, etc.), `leisure` (park, sports_centre, etc.), `shop` (supermarket, mall, convenience). Timeout configurable vía `OVERPASS_TIMEOUT_SECONDS` (default 30s).

⚠️ Tag set diverge del que usa el training del AVM ([[avm-training]] usa ~150 tags categorizados). Conciliación pendiente — ver Open items en [[catalog-service]].

### Redis ([integrations/cache/redis/cache.py](backend/catalog-service/src/app/integrations/cache/redis/cache.py))
`CacheClient` (lib infra). Expone `get`, `set`, `set_nx`, `get_json`, `set_json`, `delete`, `get_del`. El `RedisCacheAdapter` en `services/shared/adapters/` implementa el port `CachePort` consumido por los UCs.

### MinIO (scaffolded)
`integrations/storage/minio/` está scaffoldeado pero **sin código runtime** al 2026-05-21.

## Persistencia

Postgres con PostGIS vía `geoalchemy2`. Modelos en [models/location.py](backend/catalog-service/src/app/models/location.py):

- `Country` (ISO 3166-1)
- `AdminDivision` (1-nivel, unique por `(country_id, code)`)
- `Locality` (city/town/village)
- `Neighborhood` (con `geom MULTIPOLYGON SRID 4326`, `h3_cells ARRAY[VARCHAR]`, índices GIST + GIN)
- `PointOfInterest` (con `geom POINT`, `h3_index` precomputado, `(external_id, source)` único para dedup cache-aside)
- `FetchZone` (registro de celdas H3 ya consultadas a Overpass)

Todas heredan `AuditMixin` (`created_at`, `updated_at`, `created_by`, `updated_by`).

Migraciones Alembic en `src/app/migrations/versions/` — 2 migraciones aplicadas al 2026-05-21 (catálogo geo + POIs).

## Auth en el servicio

Patrón **distinto al de analytics-service**:

- **JWT viene en COOKIE** `access_token`, no en `Authorization` header — ver [auth.py:45-47](backend/catalog-service/src/app/api/deps/auth.py#L45-L47).
- **Validación vía JWKS dinámica**: `PyJWKClient(settings.KC_JWKS_URL)` se inicializa al import del módulo (líneas top-level); cada request fetches signing key (cacheado por la librería).
- **Algoritmo**: RS256. Valida `audience` (`OIDC_AUDIENCE`) e `issuer` (`KC_ISSUER`).
- **`Principal`** se construye con `sub` (UUID), `email`, `email_verified`, `roles` (extraídos de `realm_access.roles`).
- Se cachea en `request.state.principal` para no re-validar dentro del mismo request.
- `require_admin` chequea `settings.ADMIN_ROLE in principal.roles` (default `"admin"`).

Errores: `UnauthorizedError` (HTTP 401) y `ForbiddenError` (HTTP 403), ambos extends `BaseError`.

> **Nota cross-service**: la divergencia cookie-vs-header debería conciliarse a futuro. analytics-service y catalog-service usan patrones diferentes hoy. Ver `[[adr-auth-keycloak-jwt]]`.

## Cache layer compartido (`services/shared/`)

Para no acoplar cada dominio a Redis directamente:

- **Port**: [`CachePort`](backend/catalog-service/src/app/services/shared/ports/cache.py) — interfaz async (get, set, get_json, set_json, set_nx, delete, getdel).
- **Adapter**: [`RedisCacheAdapter`](backend/catalog-service/src/app/services/shared/adapters/redis_cache_adapter.py) wrappea `CacheClient` de `integrations/cache/redis/`.

Cada dominio tiene su propio `helpers/cache_keys.py` con constructores de keys (evita colisiones entre dominios y centraliza el prefijo).

## Caching strategies (por uso)

| Uso | TTL | Key |
|---|---|---|
| Forward geocode result | `CACHE_TTL_ENTITY_SECONDS` (30 d) | `cache_key_forward_geocode(query, locality_id)` |
| FetchZone freshness short-circuit | hasta `STALE_THRESHOLD_DAYS` desde `fetched_at` | `cache_key_fetch_zone(h3_index)` |
| FetchZone fetch lock | `POI_LOCK_TTL_SECONDS` (30 s) | `lock_key_fetch_zone(h3_index)` |

Las llamadas a Redis en `geo_resolution` están envueltas en `try/except` — si Redis está caído, el UC sigue contra DB / provider (cache best-effort).

## Errores

Familias en `core/exceptions/`:

| Archivo | Errores |
|---|---|
| `base.py` | `BaseError` |
| `cache.py` | errores de Redis |
| `catalog_admin.py` | errores de writes (uniqueness, FK violations) |
| `geo_catalog.py` | errores de reads |
| `geo_resolution.py` | `GeoResolutionNotFoundError`, `GeoResolutionUnavailableError`, `GeoResolutionMisconfiguredError`, `GeoResolutionBadRequestError`, `NeighborhoodResolutionError`, `CoordinatesResolutionNotFoundError` |
| `validation.py` | input validation |

`api/handlers/exception_handlers.py` registra los handlers de manera análoga a analytics-service.

## Middleware

- **CORSMiddleware** con `allow_origins=["*"]` — más permisivo que analytics, anticipando que el frontend Vue llama directo.
- **correlation_id** — mismo patrón que analytics.

## Claims

- El layout sigue el hex pattern del backend con 3 dominios paralelos: `catalog_admin`, `geo_catalog`, `geo_resolution` ([services/](backend/catalog-service/src/app/services)).
- `services/shared/` aloja el `CachePort` y `RedisCacheAdapter` reutilizados por los 3 dominios ([shared/adapters/redis_cache_adapter.py](backend/catalog-service/src/app/services/shared/adapters/redis_cache_adapter.py)).
- Auth lee el JWT desde la **cookie** `access_token`, no del header `Authorization` ([auth.py:45](backend/catalog-service/src/app/api/deps/auth.py#L45)).
- `PyJWKClient(settings.KC_JWKS_URL)` se inicializa **al import** del módulo `auth.py`, no por request ([auth.py:37](backend/catalog-service/src/app/api/deps/auth.py#L37)).
- `require_admin` chequea `settings.ADMIN_ROLE in principal.roles` con `roles` extraídos de `realm_access.roles` del JWT ([auth.py:87-103](backend/catalog-service/src/app/api/deps/auth.py#L87-L103)).
- `ResolveNeighborhoodUseCase` hace forward geocode con cache de 30 días (`CACHE_TTL_ENTITY_SECONDS`) en Redis antes de llamar Mapbox ([resolve_neighborhood.py:56-87](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_neighborhood.py#L56-L87)).
- `ResolvePoiUseCase` usa Redis `set_nx` como lock distribuido con TTL `POI_LOCK_TTL_SECONDS` (30s) para evitar fetches concurrentes a la misma zona ([resolve_poi.py:68-74](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_poi.py#L68-L74)).
- El POI fetch appendea el `h3_index` al array `h3_cells` del neighborhood después de persistir POIs — esa es la mecánica lazy-fill ([resolve_poi.py:150-156](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_poi.py#L150-L156)).
- El tag set Overpass está hardcodeado en `integrations/georef/pois/overpass.py` (~15 tags: amenity, leisure, shop subset).
- `CORSMiddleware` está configurado con `allow_origins=["*"]` ([main.py:18-23](backend/catalog-service/src/app/main.py#L18-L23)).
- Las llamadas a Redis en `geo_resolution` están envueltas en `try/except` para no romper el flujo si Redis está caído (cache best-effort).
- 2 migraciones Alembic aplicadas al 2026-05-21 ([migrations/versions/](backend/catalog-service/src/app/migrations/versions)).
