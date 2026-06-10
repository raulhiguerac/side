---
title: Arquitectura interna de properties-service
status: draft
last-verified: 2026-05-28
owners: [properties-service]
related:
  - "[[architecture]]"
  - "[[properties-service]]"
  - "[[properties-service-listing]]"
  - "[[properties-service-search]]"
  - "[[properties-service-admin]]"
  - "[[properties-service-catalog]]"
sources: [../../sources/properties-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

Hex pattern estándar del backend con tres dominios (`listing`, `search`, `admin`) + `shared`. Tres capas: `api/` (HTTP + DI), `services/<domain>/` (use cases + ports + adapters + schemas), `integrations/` (clientes a infra externa: catalog HTTP, MinIO, Redis). Persistencia vía SQLModel a Postgres+PostGIS. Adapters stateless cacheados con `@lru_cache`; UoW request-scoped.

## Layout

```
src/app/
├── api/
│   ├── deps/
│   │   ├── auth.py            # get_current_principal (cookie), require_admin
│   │   ├── db.py              # get_session
│   │   ├── listing.py         # DI del dominio listing
│   │   ├── search.py          # DI + parsers de query (cursor/filters/prefs)
│   │   └── admin.py           # DI del dominio admin
│   ├── handlers/exception_handlers.py
│   ├── middleware/correlation_id.py
│   └── routes/
│       ├── health.py
│       ├── properties.py      # dominio listing
│       ├── search.py          # dominio search
│       └── admin.py           # dominio admin (require_admin global)
├── core/
│   ├── config/settings.py     # DATABASE_URL, KC_*, REDIS_URL, TTLs, FEED_*, storage
│   ├── exceptions/            # base, listing, cache, storage
│   └── logging/
├── db/                        # session, engine
├── integrations/
│   ├── catalog/catalog_client.py   # CatalogClient (httpx)
│   ├── cache/redis/cache.py        # CacheClient
│   └── storage/minio/storage.py    # StorageClient (boto3)
├── models/property.py         # 5 tablas SQLModel + enums + AuditMixin
├── schemas/                   # base (StrictBase), principal
├── services/
│   ├── listing/               # CRUD owner + imágenes
│   ├── search/                # feed + mapa
│   ├── admin/                 # moderación + promos + precios + bulk
│   └── shared/                # ports/adapters/schemas comunes
└── workers/                   # vacío (sin Kafka hoy)
```

Reglas del layout (comunes a todos los microservicios, ver [[architecture]]):
- Use cases en `services/<domain>/use_cases/` son los **entry points** del dominio.
- Use cases dependen de **ports** (`services/<domain>/ports/` o `services/shared/ports/`), nunca de adapters concretos.
- Adapters concretos en `services/<domain>/adapters/` y `services/shared/adapters/`.
- DI resuelta en `api/deps/`: providers stateless cacheados con `@lru_cache(maxsize=1)`, UoW request-scoped por `Session`.

## Modelo de datos

Una sola migración materializa 5 tablas ([models/property.py](backend/properties-service/src/app/models/property.py)):

| Tabla | Rol |
|---|---|
| `properties` | Agregado raíz. Atributos del inmueble, precio, status, verificación, H3 (`h3_r9`/`h3_r7`), y precios estimados (`admin_estimated_price`, `ml_estimated_price`). |
| `property_locations` | 1:1 con property. PostGIS `POINT` SRID 4326 + IDs geográficos (`neighborhood_id`, `city_id`, `country_id`). Índice GiST. FK `ON DELETE CASCADE`. |
| `property_images` | N:1. URL pública, `status`, `display_order`, `is_cover`. Índice único parcial: una sola cover activa por property. |
| `property_image_upload_batches` | Transacción de subida: `expected_keys`, `status` (pending→ready→confirmed/expired/failed), `expires_at`. |
| `promoted_listings` | Promociones pagas con `starts_at`/`ends_at`/`priority`. Relación viewonly filtrada por `is_active` desde `Property.promotions`. |

Todas heredan `AuditMixin` (`created_at`, `updated_at`, `created_by`, `updated_by`, `deleted_at`, `deleted_by`).

Constraints de negocio en la tabla (no solo en Pydantic): apartamento exige `floor_number`, casa exige `total_floors`, `area_m2 > 0`, `price > 0`, `bathrooms >= 1`, `bedrooms > 0`.

## Dominio `listing`

CRUD del dueño + ciclo de imágenes. UCs en `use_cases/property_core/` (create, update, delete, get, get_my, get_public_user, set_visibility) e `use_cases/images/` (request_presigned_urls, confirm_image_uploads, delete_property_images). Ver [[properties-service-listing]].

## Dominio `search`

Feed público sin auth. `GetFeedUseCase` (orgánico + ads intercalados, paginación por cursor) y `GetFeedMapUseCase` (bbox → H3 → cache-aside por celda). Ver [[properties-service-search]].

## Dominio `admin`

Moderación (`set_status` con state machine, `verify`), `set_estimated_price` (dual admin/ML), promociones (create/delete/list), `bulk_create_properties`. Ver [[properties-service-admin]].

## Dominio `shared`

Ports y adapters transversales:
- `CatalogGateway` → `CatalogAdapter(CatalogClient)` — geo en write time.
- `CachePort` → `RedisCacheAdapter(CacheClient)` — get/set/mget/mset JSON + delete.
- `StoragePort` → `MinioStorageAdapter(StorageClient)` — URLs presignadas.
- Schemas `PropertyCardSchema` (feed/listado) y `PropertyDetailSchema` (detalle), que extraen lat/lon del POINT vía `model_validator` y calculan `is_promoted`.

## Capa de integración

| Integración | Cliente | Uso |
|---|---|---|
| **catalog-service** | `CatalogClient` (httpx, timeout 2s) | Validar barrio↔ciudad al crear; resolver lat/lon→IDs en bulk. Ver [[properties-service-catalog]]. |
| **Redis** | `CacheClient` | Cache-aside de detalle, mis-propiedades, ads, celdas de mapa; TTLs en settings. |
| **MinIO / S3** | `StorageClient` (boto3) | Generar URLs presignadas PUT para subida directa del cliente. |

## Auth

JWT del usuario llega vía **cookie** `access_token` (no header Bearer). `get_current_principal` valida contra Keycloak con `PyJWKClient`, cachea el `Principal` en `request.state`, y extrae roles de `realm_access.roles`. `get_current_principal_optional` devuelve `None` si no hay token (usado en detalle público). `require_admin` exige `settings.ADMIN_ROLE` en los roles. `UnauthorizedError`/`ForbiddenError` viven en `api/deps/auth.py`. Ver `[[adr-auth-keycloak-jwt]]`.

## Patrón de concurrencia

Las operaciones bloqueantes (repos SQL síncronos sobre `Session`) se envuelven en `run_in_threadpool` dentro de los UCs async — igual que [[analytics-service-architecture]]. El feed-mapa y el bulk usan `asyncio` para paralelizar (mget de cache, Semaphore de geo-enrichment).

## Errores y exception handling

Jerarquía en `core/exceptions/`: `base.py` (BaseError con `code`/`http_status`/`context`/`cause`), `listing.py` (~25 errores de dominio), `cache.py`, `storage.py`. Los errores SQL se traducen a errores de dominio vía `translate_db_error` ([listing/helpers/db_error_translator.py](backend/properties-service/src/app/services/listing/helpers/db_error_translator.py)). `register_exception_handlers(app)` mapea cada uno a un response HTTP.

## Claims

- El servicio define 5 tablas en `models/property.py`: `properties`, `property_locations`, `property_images`, `property_image_upload_batches`, `promoted_listings` ([models/property.py:105-318](backend/properties-service/src/app/models/property.py#L105-L318)).
- `property_locations.location` es un PostGIS `POINT` SRID 4326 con índice GiST ([models/property.py:199-217](backend/properties-service/src/app/models/property.py#L199-L217)).
- `property_images` tiene un índice único parcial que permite una sola cover activa por property ([models/property.py:227-233](backend/properties-service/src/app/models/property.py#L227-L233)).
- Los constraints apartamento→`floor_number` y casa→`total_floors` se imponen a nivel tabla con `CheckConstraint` ([models/property.py:113-122](backend/properties-service/src/app/models/property.py#L113-L122)).
- Providers stateless (`CachePort`, `CatalogGateway`, `StoragePort`) se cachean con `@lru_cache(maxsize=1)` en `api/deps/listing.py` ([deps/listing.py:34-46](backend/properties-service/src/app/api/deps/listing.py#L34-L46)).
- El UoW es request-scoped: `SqlListingUnitOfWork(session=Depends(get_session))` ([deps/listing.py:53-54](backend/properties-service/src/app/api/deps/listing.py#L53-L54)).
- `Property` guarda `admin_estimated_price` y `ml_estimated_price` en columnas separadas ([models/property.py:162-173](backend/properties-service/src/app/models/property.py#L162-L173)).
- Los precios estimados **no** se exponen en `PropertyDetailSchema` ([property_detail.py:40-70](backend/properties-service/src/app/services/shared/schemas/property_detail.py#L40-L70)).
- Las operaciones SQL bloqueantes se envuelven en `run_in_threadpool` dentro de los UCs ([create_property.py:42-44](backend/properties-service/src/app/services/listing/use_cases/property_core/create_property.py#L42-L44)).
