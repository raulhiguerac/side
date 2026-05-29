---
title: Dominio admin — properties-service
status: draft
last-verified: 2026-05-28
owners: [properties-service]
related: [[properties-service]], [[properties-service-architecture]], [[adr-estimated-price-dual-signal]], [[analytics-service]]
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

El dominio de **operación interna**: moderación (status + verificación), precios estimados (manual del admin y/o del modelo AVM), promociones pagas, y carga masiva. Todo bajo `require_admin` global en el router. La moderación impone una state machine explícita de transiciones de status.

## Use cases

| UC | Archivo | Qué hace |
|---|---|---|
| `SetPropertyStatusUseCase` | `use_cases/moderation/set_status.py` | Cambia `status` validando la state machine; invalida cache. |
| `VerifyPropertyUseCase` | `use_cases/moderation/verify.py` | Setea `verification_status` + `verified_by` / `rejection_reason`. |
| `SetEstimatedPriceUseCase` | `use_cases/estimated_price/set_estimated_price.py` | Escribe precio estimado admin **o** ML según haya principal. |
| `GetPropertiesAdminUseCase` | `use_cases/get_properties.py` | Listado admin con filtros. |
| `GetPropertyDetailAdminUseCase` | `use_cases/get_property_detail.py` | Detalle admin (sin reglas de visibilidad). |
| `CreatePromotionUseCase` | `use_cases/promotions/create.py` | Crea promoción (exige property `active`). |
| `DeletePromotionUseCase` | `use_cases/promotions/delete.py` | Desactiva la promoción activa. |
| `ListAllPromotionsUseCase` | `use_cases/promotions/list_all.py` | Lista todas las promociones. |
| `ListPromotionsByPropertyUseCase` | `use_cases/promotions/list_by_property.py` | Promos de una property. |
| `BulkCreatePropertiesUseCase` | `use_cases/bulk_create_properties.py` | Carga masiva con geo-enrichment concurrente. |

## State machine de status

`set_status` solo permite transiciones declaradas en `_ALLOWED_TRANSITIONS` ([set_status.py:12-18](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py#L12-L18)):

| Desde | Hacia |
|---|---|
| `draft` | `active` |
| `active` | `draft`, `inactive`, `sold`, `rented` |
| `inactive` | `active`, `draft` |
| `sold` | `inactive` |
| `rented` | `inactive` |

Una transición no permitida lanza `InvalidStatusTransitionError`. Tras el cambio se invalida cache de detalle, mis-propiedades del owner y celdas H3 (para que el feed-mapa refleje el cambio de visibilidad).

## Precio estimado dual

`SetEstimatedPriceUseCase` escribe en **una de dos columnas separadas** según el actor (ver [[adr-estimated-price-dual-signal]]):

- **Con `principal`** (admin vía `/admin/.../estimated-price`): escribe `admin_estimated_price` + `admin_estimated_price_at` + `updated_by`.
- **Sin `principal`** (path ML): escribe `ml_estimated_price` + `ml_estimated_price_at`.

> **Gap actual (2026-05-28)**: el path ML (principal=None) **no tiene caller**. Está diseñado para un worker que consuma `price-predicted` de [[analytics-service]], pero `workers/` está vacío. Hoy solo el path admin se ejerce.

Ambas señales se preservan por separado para servir como labels de training del modelo AVM sin que una pise a la otra.

## Bulk create

`BulkCreatePropertiesUseCase` ([bulk_create_properties.py](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py)):

1. **Geo-enrichment concurrente**: por cada record, `catalog.get_location_by_point(lat, lon)` bajo un `asyncio.Semaphore(50)`.
2. Mapea filas a modelos (`row_to_item` + `build_models`), acumulando errores por fila sin abortar el lote.
3. **Happy path**: `bulk_insert` + `commit`.
4. **Fallback**: si el bulk falla, reintenta fila por fila con `begin_nested()` / `rollback_to_savepoint()` y un solo `commit` al final.
5. Devuelve `BulkCreatePropertiesResult(inserted, errors)`.

Mismo patrón bulk-then-row-by-row que el UC batch de [[analytics-service-architecture]].

## Promociones

`promoted_listings` modela campañas con `starts_at`/`ends_at`/`priority`/`is_active`. `Property.promotions` es una relación **viewonly** filtrada por `is_active=True`, lo que alimenta `is_promoted` en `PropertyCardSchema`. Crear una promoción exige que la property esté `active` (`PropertyNotReadyForPromotionError`); no se permite más de una activa (`DuplicateActivePromotionError`).

## Claims

- Las rutas `/admin/*` están protegidas con `dependencies=[Depends(require_admin)]` a nivel router ([admin.py:41-45](backend/properties-service/src/app/api/routes/admin.py#L41-L45)).
- `set_status` valida transiciones contra `_ALLOWED_TRANSITIONS` y lanza `InvalidStatusTransitionError` si no aplica ([set_status.py:34-39](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py#L34-L39)).
- `SetEstimatedPriceUseCase` escribe `admin_estimated_price` si hay principal, `ml_estimated_price` si no ([set_estimated_price.py:26-32](backend/properties-service/src/app/services/admin/use_cases/estimated_price/set_estimated_price.py#L26-L32)).
- El path ML de `set_estimated_price` no tiene caller — `workers/` está vacío al 2026-05-28 ([workers/](backend/properties-service/src/app/workers)).
- El bulk enriquece ubicación contra catalog con un `Semaphore(50)` de concurrencia ([bulk_create_properties.py:22-23](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py#L22-L23), [bulk_create_properties.py:97-101](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py#L97-L101)).
- El bulk hace `bulk_insert` con fallback row-by-row vía `begin_nested`/`rollback_to_savepoint` ([bulk_create_properties.py:62-94](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py#L62-L94)).
- `Property.promotions` es una relación viewonly filtrada por `is_active=True` ([property.py:183-190](backend/properties-service/src/app/models/property.py#L183-L190)).
- `is_promoted` en `PropertyCardSchema` se calcula desde la presencia de promociones activas ([property_card.py:64-69](backend/properties-service/src/app/services/shared/schemas/property_card.py#L64-L69)).
