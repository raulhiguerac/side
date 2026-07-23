---
title: Dominio admin — properties-service
status: draft
last-verified: 2026-07-19
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[properties-service-architecture]]"
  - "[[adr-estimated-price-dual-signal]]"
  - "[[analytics-service]]"
  - "[[frontend-admin-panel]]"
  - "[[open-items]]"
  - "[[properties-service-bulk-create-worker]]"
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md, ../../../sources/properties-service/2026-07-16-bulk-create-sync-timeout-risk.md, ../../../sources/properties-service/2026-07-16-bulk-create-owner-id-resolution.md, ../../../sources/properties-service/2026-07-19-bulk-create-worker-streaming-csv.md]
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
| `BulkCreatePropertiesUseCase` | `use_cases/bulk_create_properties.py` | Carga masiva con geo-enrichment concurrente. |

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

`BulkCreatePropertiesUseCase` — **relocada** de `services/admin/use_cases/bulk_create_properties.py` a [`workers/bulk_create_properties.py`](backend/properties-service/src/app/workers/bulk_create_properties.py) (2026-07-19), en reconstrucción activa. Ver [[properties-service-bulk-create-worker]] para el detalle técnico (streaming desde MinIO, parseo CSV, algoritmo de paridad de comillas).

**Flujo nuevo, parcialmente conectado**:

1. Lee el CSV desde MinIO en streaming (`iter_csv_rows`) — nunca carga el archivo completo en memoria, y ya devuelve dicts resueltos (no líneas crudas).
2. Acumula filas en batches de 2500, con flush final para el remanente.
3. Por batch, `_process_batch` arma un `id` de correlación por fila (índice dentro del batch), llama `catalog.get_locations_bulk(points)` **una vez por batch** (no una llamada HTTP por fila), y mergea el resultado de vuelta en cada dict por `id`. Filas con lat/lon inválido o sin match de ubicación van a `errors` sin abortar el batch.
4. **Sin conectar todavía**: el output de `_process_batch` (`enriched: list[dict], errors: list[str]`) no se pasa a `row_to_item`/`build_models`/`bulk_insert` — el código viejo que hacía eso (`asyncio.gather` + `Semaphore(50)` + `_enrich_location`) sigue debajo en `execute()`, ahora referenciando variables que no existen (`records`, `sem`) — es código muerto pendiente de reconciliar, no un fallback funcional.

El patrón bulk-then-row-by-row para el insert final (`bulk_insert` con fallback `begin_nested`/`rollback_to_savepoint`, mismo patrón que el UC batch de [[analytics-service-architecture]]) sigue existiendo en el archivo pero **desconectado** de la nueva ruta de entrada — mirá el código del archivo, no asumas que este flujo end-to-end ya funciona.

> **Riesgo detectado (2026-07-16), pendiente de refactor — ver `open-items.md`, marcado IMPORTANTE**: `execute()` corre **síncrono end-to-end dentro del ciclo del request HTTP**, incluyendo el geo-enrichment contra catalog-service (paso 1) y el `commit()` (paso 3/4) — la respuesta al front solo llega después de que el commit ya se ejecutó. El timeout del cliente (`propertiesApi`, 8s) puede no alcanzar para CSVs de más de un puñado de filas, dado el acumulado de latencia de red hacia catalog-service por cada fila. Refactor propuesto (no implementado): patrón `202 { batch_id }` + procesamiento en background + endpoint de polling de status, con el gotcha de que las dependencias `yield` (UoW/sesión) de FastAPI se cierran antes de que corra un `BackgroundTask` — el worker necesitaría abrir su propia sesión. Ver [[frontend-admin-panel]] para el lado consumidor (el modal de importación que expuso el problema).
>
> **Update 2026-07-19**: la clase se movió a `workers/bulk_create_properties.py` (antes vivía en `services/admin/use_cases/`) — el nombre del módulo sugiere el refactor a background, pero **no hay confirmación** de que la ruta HTTP ya la invoque vía `BackgroundTasks` en vez de `await`-earla inline. No asumir resuelto hasta verificar `api/routes/admin.py`.

> **Segundo hallazgo (2026-07-16), también pendiente — marcado IMPORTANTE**: `build_models()` (`seed_mapper.py`) llama `Property(owner_id=owner_id, ...)` con `owner_id=principal.sub` — el mismo UUID que `created_by`. Todas las propiedades importadas en bloque quedan "de propiedad" del admin que corrió el import, apareciendo en su propio `GET /properties/me`. `created_by=principal.sub` está bien (audita quién ejecutó el import). `owner_id` está mal: debería resolver a la cuenta real del dueño. **Decisión tomada**: resolver por **email** contra `Account.email` en users-service (único+indexado, sin migración) — se descartó cédula porque ese campo no existe hoy en `users-service` (solo `account_id`/`email` son identificadores únicos en `models/account.py`). El CSV necesitaría una columna de email por fila; qué pasa si no matchea ninguna cuenta (¿crear placeholder? ¿rechazar fila?) queda sin decidir. La trazabilidad de qué `property_id`s salieron de qué import puede resolverse con la misma entidad de batch del refactor async de arriba, sin mecanismo aparte.

## Promociones

`promoted_listings` modela campañas con `starts_at`/`ends_at`/`priority`/`is_active`. `Property.promotions` es una relación **viewonly** filtrada por `is_active=True`, lo que alimenta `is_promoted` en `PropertyCardSchema`. Crear una promoción exige que la property esté `active` (`PropertyNotReadyForPromotionError`); no se permite más de una activa (`DuplicateActivePromotionError`).

## Claims

- Las rutas `/admin/*` están protegidas con `dependencies=[Depends(require_admin)]` a nivel router ([admin.py:43-47](backend/properties-service/src/app/api/routes/admin.py#L43-L47)).
- `set_status` valida transiciones contra `_ALLOWED_TRANSITIONS` y lanza `InvalidStatusTransitionError` si no aplica ([set_status.py:39-44](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py#L39-L44)).
- `SetEstimatedPriceUseCase` escribe `admin_estimated_price` si hay principal, `ml_estimated_price` si no ([set_estimated_price.py:26-32](backend/properties-service/src/app/services/admin/use_cases/estimated_price/set_estimated_price.py#L26-L32)).
- El path ML de `set_estimated_price` no tiene caller — `workers/` está vacío al 2026-05-28 ([workers/](backend/properties-service/src/app/workers)).
- **Desactualizado desde 2026-07-19, no confirmado contra código actual**: `BulkCreatePropertiesUseCase` se relocó a `workers/bulk_create_properties.py`; los claims de abajo sobre `Semaphore(50)` por fila, la ruta síncrona (`admin.py`) y ausencia de `BackgroundTasks` describían el archivo en su ubicación/forma vieja (`services/admin/use_cases/`) y **no fueron re-verificados** contra el nuevo flujo de streaming+batch — ver [[properties-service-bulk-create-worker]] para lo que sí está verificado del código nuevo.
- El bulk enriquece ubicación contra catalog con un `Semaphore(50)` de concurrencia — **código viejo, ver nota de arriba; el flujo nuevo llama `catalog.get_locations_bulk` una vez por batch de 2500, no una vez por fila** ([bulk_create_properties.py](backend/properties-service/src/app/workers/bulk_create_properties.py)).
- El bulk hace `bulk_insert` con fallback row-by-row vía `begin_nested`/`rollback_to_savepoint` — sigue en el archivo pero desconectado del nuevo entry point (`execute()` no llega a este código todavía) ([bulk_create_properties.py](backend/properties-service/src/app/workers/bulk_create_properties.py)).
- `build_models()` setea `owner_id=owner_id` con el valor `principal.sub` pasado desde `execute()` — el mismo UUID que `created_by` ([seed_mapper.py:210-212](backend/properties-service/src/app/services/admin/helpers/seed_mapper.py#L210-L212), [bulk_create_properties.py:54-56](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py#L54-L56)).
- `Account` en users-service tiene `account_id` y `email` como únicos identificadores indexados/únicos — no existe ningún campo de documento de identidad (cédula) ([account.py:37-53](backend/users-service/src/app/models/account.py#L37-L53)).
- `Property.promotions` es una relación viewonly filtrada por `is_active=True` ([property.py:183-190](backend/properties-service/src/app/models/property.py#L183-L190)).
- `is_promoted` en `PropertyCardSchema` se calcula desde la presencia de promociones activas ([property_card.py:64-69](backend/properties-service/src/app/services/shared/schemas/property_card.py#L64-L69)).
