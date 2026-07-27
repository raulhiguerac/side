---
title: Dominio admin — properties-service
status: draft
last-verified: 2026-07-27
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[properties-service-architecture]]"
  - "[[adr-estimated-price-dual-signal]]"
  - "[[adr-bulk-idempotent-external-id]]"
  - "[[analytics-service]]"
  - "[[frontend-admin-panel]]"
  - "[[open-items]]"
  - "[[properties-service-bulk-create-worker]]"
  - "[[properties-service-users]]"
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md, ../../../sources/properties-service/2026-07-16-bulk-create-sync-timeout-risk.md, ../../../sources/properties-service/2026-07-16-bulk-create-owner-id-resolution.md, ../../../sources/properties-service/2026-07-19-bulk-create-worker-streaming-csv.md, ../../../sources/properties-service/2026-07-27-bulk-async-import-worker.md]
---

## TL;DR

El dominio de **operación interna**: moderación (status + verificación), precios estimados (manual del admin y/o del modelo AVM), promociones pagas, y carga masiva. Todo bajo `require_admin` global en el router. La moderación impone una state machine explícita de transiciones de status.

## Use cases

| UC | Archivo | Qué hace |
|---|---|---|
| `SetPropertyStatusUseCase` | `use_cases/moderation/set_status.py` | Cambia `status` validando la state machine; invalida cache. |
| `VerifyPropertyUseCase` | `use_cases/moderation/verify.py` | Cambia `verification_status` validando su propia state machine; **no** setea `verified_by` (campo muerto — el UC no recibe `principal`). |
| `SetEstimatedPriceUseCase` | `use_cases/estimated_price/set_estimated_price.py` | Escribe precio estimado admin **o** ML según haya principal. |
| `GetPropertiesAdminUseCase` | `use_cases/get_properties.py` | Listado admin con filtros. |
| `GetPropertyDetailAdminUseCase` | `use_cases/get_property_detail.py` | Detalle admin (sin reglas de visibilidad). |
| `CreatePromotionUseCase` | `use_cases/promotions/create.py` | Crea promoción (exige property `active`). |
| `DeletePromotionUseCase` | `use_cases/promotions/delete.py` | Desactiva la promoción activa. |
| `ListAllPromotionsUseCase` | `use_cases/promotions/list_all.py` | Lista todas las promociones. |
| `ListPromotionsByPropertyUseCase` | `use_cases/promotions/list_by_property.py` | Promos de una property. |
| `RequestBulkUploadUrlUseCase` | `use_cases/request_bulk_upload_url.py` | Emite la presigned PUT para subir el CSV a MinIO; no persiste nada. |
| `BulkCreatePropertiesUseCase` | `use_cases/bulk_create_properties.py` | **Solo encola**: valida el retry, crea la fila en `bulk_jobs`, devuelve `batch_id`. |
| `GetBulkJobStatusUseCase` | `use_cases/get_bulk_job_status.py` | Status + errores del job; marca `failed` los `pending` vencidos. |

## State machine de status

`set_status` solo permite transiciones declaradas en `_ALLOWED_TRANSITIONS` ([set_status.py:17-23](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py#L17-L23)):

| Desde | Hacia |
|---|---|
| `draft` | `active` |
| `active` | `draft`, `inactive`, `sold`, `rented` |
| `inactive` | `active`, `draft` |
| `sold` | `inactive` |
| `rented` | `inactive` |

Una transición no permitida lanza `InvalidStatusTransitionError`. Tras el cambio se invalida cache de detalle, mis-propiedades del owner y celdas H3 (para que el feed-mapa refleje el cambio de visibilidad).

### State machine de `verification_status` (independiente de la de arriba)

`VerifyPropertyUseCase` tiene su **propia** `_ALLOWED_TRANSITIONS` sobre `VerificationStatus`, separada de la de `ListingStatus` de arriba — no documentada hasta ahora:

| Desde | Hacia |
|---|---|
| `unverified` | `pending` |
| `pending` | `verified`, `rejected` |
| `rejected` | `pending` |
| `verified` | — (terminal, sin salida) |

Una transición no permitida lanza el mismo `InvalidStatusTransitionError` que `set_status`. El UC no recibe `principal` en su firma (`execute(*, property_id, request)`), así que el campo `verified_by` del modelo `Property` nunca se escribe desde este flujo — queda muerto.

## Precio estimado dual

`SetEstimatedPriceUseCase` escribe en **una de dos columnas separadas** según el actor (ver [[adr-estimated-price-dual-signal]]):

- **Con `principal`** (admin vía `/admin/.../estimated-price`): escribe `admin_estimated_price` + `admin_estimated_price_at` + `updated_by`.
- **Sin `principal`** (path ML): escribe `ml_estimated_price` + `ml_estimated_price_at`.

> **Gap actual (2026-05-28)**: el path ML (principal=None) **no tiene caller**. Está diseñado para un worker que consuma `price-predicted` de [[analytics-service]], pero `workers/` está vacío. Hoy solo el path admin se ejerce.

Ambas señales se preservan por separado para servir como labels de training del modelo AVM sin que una pise a la otra.

## Bulk create

**Resuelto end-to-end el 2026-07-27.** El dominio admin ya no ejecuta el import: `BulkCreatePropertiesUseCase` (`use_cases/bulk_create_properties.py`) **solo encola** — valida el retry, crea la fila en `bulk_jobs` y devuelve el `batch_id`. El procesamiento vive en `BulkCreatePropertiesWorker` (`workers/bulk_create_properties_worker.py`), que corre en background. Ver [[properties-service-bulk-create-worker]] para el detalle técnico completo.

Flujo en tres pasos: `POST /admin/properties/bulk/upload-url` (201, presigned PUT) → el front sube el CSV directo a MinIO → `POST /admin/properties/bulk` con la `storage_key` (202 + `batch_id`, agenda `BackgroundTasks`) → `GET /admin/properties/bulk/{job_id}/status` para polling.

Responsabilidades del UC de encolado:

- Si es un retry: verifica que el job exista, que **no sea a su vez un retry** (`RetryOfRetryNotAllowedError`) y que no esté vencido (`BulkJobExpiredError`, 409). Hereda `expires_at` del original en vez de renovarlo, para que encadenar reintentos no extienda la ventana indefinidamente.
- Si es nuevo: `expires_at = now + 60 días` (`_RETRY_WINDOW`).

> **Riesgo de timeout (2026-07-16) — cerrado.** El endpoint corría síncrono end-to-end dentro del request y podía superar el timeout de 8s del front. Resuelto con el patrón `202 + batch_id` + `BackgroundTasks` + endpoint de polling. El gotcha que se había anticipado se confirmó y se manejó: el runner abre su propia `Session(engine)` porque las dependencias `yield` de FastAPI se cierran antes de que corra el `BackgroundTask`. Ver [[frontend-admin-panel]] para el lado consumidor.

> **`owner_id` = el admin importador (2026-07-16) — cerrado.** El CSV ahora trae una columna `email` por fila y el worker resuelve `email → account_id` contra users-service (ver [[properties-service-users]]), poblando `Property.owner_id` con la cuenta real. `created_by` sigue siendo `principal.sub` (auditoría de quién ejecutó el import), que siempre estuvo bien. Un email sin cuenta activa **no** se asigna a nadie: la fila falla con `"owner not resolved for email"` y queda registrada en `bulk_jobs.errors`.

> **Trazabilidad — sigue abierta.** `Property.bulk_job_id` existe como FK nullable indexada ([listing.py:90](backend/properties-service/src/app/models/listing.py#L90)) pero **ningún código la escribe**, así que hoy no se puede saber qué properties salieron de qué import. Es también la pieza que faltaba para la acción de "redo" (soft-delete por batch) que nunca se construyó — ver [[adr-bulk-idempotent-external-id]].

## Promociones

`promoted_listings` modela campañas con `starts_at`/`ends_at`/`priority`/`is_active`. `Property.promotions` es una relación **viewonly** filtrada por `is_active=True`, lo que alimenta `is_promoted` en `PropertyCardSchema`. Crear una promoción exige que la property esté `active` (`PropertyNotReadyForPromotionError`); no se permite más de una activa (`DuplicateActivePromotionError`).

## Claims

- Las rutas `/admin/*` están protegidas con `dependencies=[Depends(require_admin)]` a nivel router ([admin.py:43-47](backend/properties-service/src/app/api/routes/admin.py#L43-L47)).
- `set_status` valida transiciones contra `_ALLOWED_TRANSITIONS` y lanza `InvalidStatusTransitionError` si no aplica ([set_status.py:39-44](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py#L39-L44)).
- `SetEstimatedPriceUseCase` escribe `admin_estimated_price` si hay principal, `ml_estimated_price` si no ([set_estimated_price.py:26-32](backend/properties-service/src/app/services/admin/use_cases/estimated_price/set_estimated_price.py#L26-L32)).
- El path ML de `set_estimated_price` no tiene caller — `workers/` está vacío al 2026-05-28 ([workers/](backend/properties-service/src/app/workers)).
- `BulkCreatePropertiesUseCase` (`use_cases/bulk_create_properties.py`) solo encola: crea la fila en `bulk_jobs` y devuelve el `batch_id`; no procesa el CSV ([bulk_create_properties.py](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py)).
- Un retry hereda `expires_at` del job original en vez de recibir una ventana nueva, y se rechaza con `RetryOfRetryNotAllowedError` si el target ya es un retry o con `BulkJobExpiredError` si está vencido ([bulk_create_properties.py](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py)).
- `POST /admin/properties/bulk` responde `202` con `batch_id` y agenda el worker vía `BackgroundTasks`; el procesamiento no ocurre dentro del request ([admin.py](backend/properties-service/src/app/api/routes/admin.py)).
- `build_models()` recibe `owner_id` resuelto desde el `email` de la fila del CSV vía `email_cache`, y `created_by=principal.sub` — ya no son el mismo UUID ([orm_objects.py](backend/properties-service/src/app/workers/helpers/mapping/orm_objects.py), [seed_mapper.py](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py)).
- `Property.bulk_job_id` está declarada como FK nullable indexada pero ningún código del servicio la escribe ([listing.py:90](backend/properties-service/src/app/models/listing.py#L90)).
- `Account` en users-service tiene `account_id` y `email` como únicos identificadores indexados/únicos — no existe ningún campo de documento de identidad (cédula) ([account.py:37-53](backend/users-service/src/app/models/account.py#L37-L53)).
- `Property.promotions` es una relación viewonly filtrada por `is_active=True` ([listing.py](backend/properties-service/src/app/models/listing.py)).
- `is_promoted` en `PropertyCardSchema` se calcula desde la presencia de promociones activas ([property_card.py:64-69](backend/properties-service/src/app/services/shared/schemas/property_card.py#L64-L69)).
