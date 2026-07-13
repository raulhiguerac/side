---
title: Dominio listing — properties-service
status: draft
last-verified: 2026-07-13
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[properties-service-architecture]]"
  - "[[properties-service-catalog]]"
  - "[[adr-image-upload-presigned-batch]]"
  - "[[adr-owner-list-cache-invalidation]]"
  - "[[adr-cache-optional-layer]]"
  - "[[adr-property-edit-fixed-fields]]"
  - "[[adr-single-listing-type-per-property]]"
sources:
  - ../../../sources/properties-service/2026-05-28-foundational-exploration.md
  - ../../../sources/properties-service/2026-06-22-public-storefront-cache-invalidation.md
  - ../../../sources/properties-service/2026-06-25-public-user-properties-pagination.md
  - ../../../sources/properties-service/2026-07-13-owner-listings-order-by-created-at.md
---

## TL;DR

El dominio del **dueño** sobre sus propiedades: crear, editar, borrar, controlar visibilidad y administrar fotos. Las escrituras validan geografía contra [[catalog-service]] en write time y computan los índices H3 localmente. Las fotos se suben **directo a object storage** vía URLs presignadas con un protocolo de batch (request → upload → confirm).

## Use cases

| UC | Archivo | Qué hace |
|---|---|---|
| `CreatePropertyUseCase` | `use_cases/property_core/create_property.py` | Valida barrio↔ciudad contra catalog, computa H3, persiste `Property` + `PropertyLocation`. |
| `UpdatePropertyUseCase` | `use_cases/property_core/update_property.py` | Patch parcial; re-valida geo y re-computa H3 si cambia location; invalida cache. Acepta cambiar cualquier campo (incluida `location`) — el frontend restringe cuáles expone como editables, ver [[adr-property-edit-fixed-fields]]. |
| `DeletePropertyUseCase` | `use_cases/property_core/delete_property.py` | **Soft-delete**: `status=inactive` + `deleted_at`/`deleted_by`; no borra filas. Invalida cache. |
| `GetPropertyUseCase` | `use_cases/property_core/get_property.py` | Detalle con cache-aside; reglas de visibilidad por status/owner. |
| `GetMyPropertiesUseCase` | `use_cases/property_core/get_my_properties.py` | Lista del owner — todos los estados, cache por usuario (`client_properties`), ordenada por `created_at desc`. |
| `GetPublicUserPropertiesUseCase` | `use_cases/property_core/get_public_user_properties.py` | Vitrina pública de otro usuario — solo `active`, paginada por offset y ordenada por `created_at desc`, devuelve `PublicUserPropertiesResponse(items, has_more)`, cache por página. |
| `SetPropertyVisibilityUseCase` | `use_cases/property_core/set_property_visibility.py` | Toggle de visibilidad del dueño. |
| `RequestPresignedUrlsUseCase` | `use_cases/images/request_presigned_urls.py` | Crea batch + URLs presignadas PUT. |
| `ConfirmImageUploadsUseCase` | `use_cases/images/confirm_image_uploads.py` | Valida batch y materializa `PropertyImage`. |
| `DeletePropertyImagesUseCase` | `use_cases/images/delete_property_images.py` | Borra imágenes del owner. |

Ports: `property_repository`, `property_location_repository`, `property_images_repository`, `unit_of_work` (en `services/listing/ports/`). Adapters SQL en `services/listing/adapters/`.

## Flujo de `CreateProperty.execute`

1. Toma `location` del request y llama `catalog.get_neighborhood(neighborhood_id)`.
2. Si `guard.locality_id != loc.city_id` → `InconsistentLocationError` (el barrio no pertenece a la ciudad declarada).
3. `compute_h3(lat, lon)` → `(h3_r9, h3_r7)` localmente.
4. `build_models` arma `Property` (status `draft`, verificación `unverified`, `owner_id = principal.sub`) y `PropertyLocation` (POINT desde `shapely`).
5. `add(property)` + `add(location)` + `commit()`, todo bajo `run_in_threadpool`. Si falla → `rollback()` + `translate_db_error`.
6. Devuelve el `uuid` de la propiedad.

La propiedad nace en `draft` — no es visible en el feed hasta que un admin la pase a `active` (ver [[properties-service-admin]]).

## Visibilidad en `GetProperty`

- Cache-aside: primero `cache.get_json(properties:detail:<id>)`.
- Si miss, lee de DB. `None` → `PropertyNotFoundError`.
- **Regla de visibilidad**: si `status != active` y el requester no es el owner → `PropertyNotFoundError` (no se filtra existencia de drafts ajenos).
- Solo se cachean propiedades `active` (TTL `CACHE_TTL_PROPERTY_SECONDS` = 6h).

## Caching e invalidación de las listas del owner

Hay **dos** listas cacheadas del dueño, con scope distinto:

| Lista | Key | Filtro | Auth |
|---|---|---|---|
| Mis propiedades (`/me`) | `properties:user:{id}` (`client_properties`) | todos los estados | JWT → `principal.sub` |
| Vitrina pública (`/users/{id}`) | `properties:user:{id}:public:{offset}` (`public_user_properties`) | solo `active` | sin auth, `user_id` del path |

La pública pagina por **offset** con truco `+1`: `PUBLIC_PROPERTIES_PAGE_SIZE = 21` en settings (fetch 21 filas; si `len == 21` → `has_more=True`, se devuelven solo los primeros 20). El offset va **en la key** — sin él, la página 2 devolvería la data cacheada de la 1. El resultado vacío también se cachea (`if cached is not None`) para que un usuario sin listings no pegue a DB en cada request. La respuesta es `PublicUserPropertiesResponse(items: list[PropertyCardSchema], has_more: bool)`; el cache guarda el dict completo incluyendo `has_more`.

**Invalidación por prefijo.** Como un cambio de membresía corre la posición de todas las propiedades siguientes, no se puede invalidar una sola página: `delete_pattern("properties:user:{id}:public:*")` borra **todas** las páginas del dueño (`SCAN` + `DEL`) y se re-cachean on-demand. Cada UC de escritura relevante hace **dos operaciones**: `delete([keys exactas])` + `delete_pattern(prefijo público)`. Detalle y alternativas en [[adr-owner-list-cache-invalidation]]; la degradación silenciosa ante Redis caído sigue [[adr-cache-optional-layer]].

**8 UCs invalidan la vitrina pública** (criterio: cambian la membresía del set `active` o un campo que renderiza `PropertyCardSchema` — precio/datos, fotos con `is_cover`, `is_promoted`):

- listing: `update_property`, `delete_property`, `set_property_visibility`, `confirm_image_uploads`, `delete_property_images`
- admin: `moderation/set_status`, `promotions/create`, `promotions/delete`

**Excluidos a propósito**: `verify` (la card no expone `verification_status`) y `create_property` (nace `draft`, entra al set público recién al publicarse vía `set_visibility`/`set_status`, que ya invalidan).

## Flujo de imágenes (presigned + batch)

Protocolo en tres pasos para subir directo a MinIO sin pasar bytes por el servicio (ver [[adr-image-upload-presigned-batch]]):

1. **Request** (`POST /properties/images/presigned-urls`):
   - Verifica ownership + `check_image_count` (no exceder `MAX_IMAGES_PER_PROPERTY`).
   - Genera `count` keys `{property_id}/{uuid}`.
   - Crea `PropertyImageUploadBatch` (`status=pending`, `expected_keys`, `expires_at` = now + TTL).
   - Pide URLs presignadas PUT al storage; si falla, marca batch `failed`. Si ok, marca `ready`.
   - Devuelve `batch_id` + items (`upload_url`, `public_url`, `key`).
2. **Upload**: el cliente sube cada archivo con PUT directo a `upload_url` (no toca el backend).
3. **Confirm** (`POST /properties/{id}/images/confirm`):
   - Valida ownership, que el batch exista y sea consistente con la property, que no esté expirado, y que esté en estado `ready`.
   - Valida que `confirmed_keys ⊆ expected_keys`.
   - Inserta un `PropertyImage` por key confirmada (URL pública = `base_url/bucket/key`), marca batch `confirmed`.
   - Invalida cache (detalle, mis-propiedades, ids de imágenes).

Estados del batch: `pending → ready → confirmed`, con ramas `expired` (TTL vencido) y `failed` (error de storage o confirm sobre batch pending).

## Errores de dominio

`core/exceptions/listing.py` define ~25 errores. Relevantes a listing: `PropertyNotFoundError`, `PropertyForbiddenError`, `InconsistentLocationError`, `InvalidLocationError`, `LocationNotResolvedError`, `ImageCountExceededError`, `ImageNotOwnedError`, `BatchNotFoundError`, `BatchExpiredError`, `BatchInvalidStateError`, `BatchNotConsistentError`, `CreatePropertyError`, `DeletePropertyError`.

## Claims

- Al crear, si el barrio no pertenece a la ciudad declarada se lanza `InconsistentLocationError` comparando `guard.locality_id` con `loc.city_id` ([create_property.py:27-31](backend/properties-service/src/app/services/listing/use_cases/property_core/create_property.py#L27-L31)).
- Una propiedad nueva nace con `status=draft` y `verification_status=unverified` ([create_property.py:69-70](backend/properties-service/src/app/services/listing/use_cases/property_core/create_property.py#L69-L70)).
- Los índices H3 se computan localmente con `h3.latlng_to_cell` en resoluciones 9 y 7 ([geometry.py:11-13](backend/properties-service/src/app/services/shared/helpers/geometry.py#L11-L13)).
- `GetProperty` solo cachea propiedades con `status=active` ([get_property.py:54-62](backend/properties-service/src/app/services/listing/use_cases/property_core/get_property.py#L54-L62)).
- Una propiedad no-active solo es visible para su owner; si no, `PropertyNotFoundError` ([get_property.py:48-50](backend/properties-service/src/app/services/listing/use_cases/property_core/get_property.py#L48-L50)).
- El upload usa URLs presignadas: el batch pasa por `pending → ready` antes de devolverse al cliente ([request_presigned_urls.py:74-82](backend/properties-service/src/app/services/listing/use_cases/images/request_presigned_urls.py#L74-L82)).
- Confirm rechaza si `confirmed_keys` no es subconjunto de `expected_keys` con `BatchNotConsistentError` ([confirm_image_uploads.py:74-81](backend/properties-service/src/app/services/listing/use_cases/images/confirm_image_uploads.py#L74-L81)).
- Confirm exige estado `ready`; un batch `pending` se marca `failed` ([confirm_image_uploads.py:65-72](backend/properties-service/src/app/services/listing/use_cases/images/confirm_image_uploads.py#L65-L72)).
- `create_count` está acotado a `[1, MAX_IMAGES_PER_PROPERTY]` por el schema ([listing_schemas.py:90-92](backend/properties-service/src/app/services/listing/schemas/listing_schemas.py#L90-L92)).
- `DeleteProperty` es soft-delete: setea `status=inactive` + `deleted_at` + `deleted_by`, no borra filas ([delete_property.py:21-23](backend/properties-service/src/app/services/listing/use_cases/property_core/delete_property.py#L21-L23)).
- `GetPublicUserProperties` devuelve solo `status=active`, paginadas por offset con `LIMIT PUBLIC_PROPERTIES_PAGE_SIZE` (21) — la DB devuelve hasta 21 filas, el UC retorna las primeras 20 y deduce `has_more` del conteo ([sql_property_repository.py:37-52](backend/properties-service/src/app/services/listing/adapters/sql_property_repository.py#L37-L52), [get_public_user_properties.py](backend/properties-service/src/app/services/listing/use_cases/property_core/get_public_user_properties.py)).
- La respuesta de la vitrina pública es `PublicUserPropertiesResponse(items, has_more)` — el cache guarda el dict completo incluyendo `has_more`; trata `cached is not None` como hit válido para usuarios sin listings ([property_card.py](backend/properties-service/src/app/services/shared/schemas/property_card.py)).
- Los 8 UCs de escritura que tocan el set público invalidan con `delete_pattern(public_user_properties_pattern(owner))` además de las keys exactas; `verify` y `create_property` no ([cache_keys.py](backend/properties-service/src/app/services/shared/helpers/cache_keys.py)).
- El endpoint público acota el offset a `>= 0` vía `Query(ge=0)` y default 0 ([properties.py](backend/properties-service/src/app/api/routes/properties.py)).
- `get_user_properties` y `get_public_user_properties` ordenan por `Property.created_at.desc()` — en la paginada, el `order_by` va antes de `limit()`/`offset()`, necesario para que la paginación por offset sea estable ([sql_property_repository.py](backend/properties-service/src/app/services/listing/adapters/sql_property_repository.py)).
- `Property` es 1 fila = 1 `listing_type` fijo; no hay relación entre filas que representen el mismo inmueble bajo distintas modalidades (venta/arriendo) — ver [[adr-single-listing-type-per-property]] ([models/property.py](backend/properties-service/src/app/models/property.py)).
