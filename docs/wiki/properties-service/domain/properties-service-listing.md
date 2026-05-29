---
title: Dominio listing — properties-service
status: draft
last-verified: 2026-05-28
owners: [properties-service]
related: [[properties-service]], [[properties-service-architecture]], [[properties-service-catalog]], [[adr-image-upload-presigned-batch]]
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

El dominio del **dueño** sobre sus propiedades: crear, editar, borrar, controlar visibilidad y administrar fotos. Las escrituras validan geografía contra [[catalog-service]] en write time y computan los índices H3 localmente. Las fotos se suben **directo a object storage** vía URLs presignadas con un protocolo de batch (request → upload → confirm).

## Use cases

| UC | Archivo | Qué hace |
|---|---|---|
| `CreatePropertyUseCase` | `use_cases/property_core/create_property.py` | Valida barrio↔ciudad contra catalog, computa H3, persiste `Property` + `PropertyLocation`. |
| `UpdatePropertyUseCase` | `use_cases/property_core/update_property.py` | Patch parcial; re-valida geo y re-computa H3 si cambia location; invalida cache. |
| `DeletePropertyUseCase` | `use_cases/property_core/delete_property.py` | Borra la propiedad (cascade a location/imágenes) e invalida cache. |
| `GetPropertyUseCase` | `use_cases/property_core/get_property.py` | Detalle con cache-aside; reglas de visibilidad por status/owner. |
| `GetMyPropertiesUseCase` | `use_cases/property_core/get_my_properties.py` | Lista del owner (cache por usuario). |
| `GetPublicUserPropertiesUseCase` | `use_cases/property_core/get_public_user_properties.py` | Lista pública de otro usuario. |
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
