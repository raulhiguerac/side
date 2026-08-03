---
title: Dominio admin — properties-service
status: draft
last-verified: 2026-08-02
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[properties-service-architecture]]"
  - "[[adr-estimated-price-dual-signal]]"
  - "[[adr-bulk-idempotent-external-id]]"
  - "[[adr-admin-offset-pagination]]"
  - "[[adr-verification-reversible-lifecycle]]"
  - "[[analytics-service]]"
  - "[[frontend-admin-panel]]"
  - "[[open-items]]"
  - "[[properties-service-bulk-create-worker]]"
  - "[[properties-service-users]]"
  - "[[properties-service-search]]"
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md, ../../../sources/properties-service/2026-07-16-bulk-create-sync-timeout-risk.md, ../../../sources/properties-service/2026-07-16-bulk-create-owner-id-resolution.md, ../../../sources/properties-service/2026-07-19-bulk-create-worker-streaming-csv.md, ../../../sources/properties-service/2026-07-27-bulk-async-import-worker.md, ../../../sources/properties-service/2026-07-28-bulk-import-smoke-test.md, ../../../sources/properties-service/2026-07-29-moderation-state-machines-block-imports.md, ../../../sources/properties-service/2026-08-01-bulk-import-pending-verification.md, ../../../sources/properties-service/2026-08-02-moderation-lifecycle-verified-not-terminal.md]
---

## TL;DR

El dominio de **operación interna**: moderación (status + verificación), precios estimados (manual del admin y/o del modelo AVM), promociones pagas, y carga masiva. Todo bajo `require_admin` global en el router. La moderación impone una state machine explícita de transiciones de status.

## Use cases

| UC | Archivo | Qué hace |
|---|---|---|
| `SetPropertyStatusUseCase` | `use_cases/moderation/set_status.py` | Cambia `status` validando la state machine; invalida cache. |
| `VerifyPropertyUseCase` | `use_cases/moderation/verify.py` | Cambia `verification_status` validando su propia state machine; firma `verified_by` y `updated_by` con el admin. |
| `SetEstimatedPriceUseCase` | `use_cases/estimated_price/set_estimated_price.py` | Escribe precio estimado admin **o** ML según haya principal. |
| `GetPropertiesAdminUseCase` | `use_cases/get_properties.py` | Listado admin paginado con filtros + `total`. |
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

`VerifyPropertyUseCase` tiene su **propia** `_ALLOWED_TRANSITIONS` sobre `VerificationStatus`, separada de la de `ListingStatus` de arriba:

| Desde | Hacia |
|---|---|
| `unverified` | `pending` |
| `pending` | `verified`, `rejected` |
| `rejected` | `pending` |
| `verified` | `pending`, `rejected` |

Una transición no permitida lanza el mismo `InvalidStatusTransitionError` que `set_status`.

**`verified` no es terminal** (desde el 2026-08-02, ver [[adr-verification-reversible-lifecycle]]): una property aprobada que después viola las normas se revoca a `rejected`, y un cambio de fotos la devuelve a `pending`. Lo único prohibido desde ahí es volver a `unverified`, que existe solo como estado inicial y al que no apunta ninguna transición.

Dar de baja una publicación **no** vive en este eje: es `status: active → inactive`, y funciona como takedown real porque la máquina del dueño solo hace `draft ↔ active` (ver [[properties-service-listing]]).

### Quién moderó queda firmado

`execute()` recibe `principal` y escribe `updated_by` siempre. `verified_by` se firma cuando la verificación queda **resuelta** (`verified` o `rejected`) y se **limpia** al reencolar a `pending`, junto con `rejection_reason` — una property sin resolver no puede tener aprobador.

`verified_by` se sostiene aparte de `updated_by` porque este último lo pisa cualquier escritura posterior, incluida la del dueño editando el precio. `SetPropertyStatusUseCase` también recibe `principal` y escribe `updated_by`; antes las dos acciones de moderación eran anónimas en la DB.

Lo que sigue faltando es **cuándo**: no existe `verified_at`, y `updated_at` lo pisa la siguiente escritura (ver [[open-items]]).

### `rejection_reason` está atado al target, y la regla vive en el schema

`VerifyPropertyRequest` valida con un `model_validator(mode="after")`: el motivo es **obligatorio** al rechazar y **prohibido** en cualquier otro target, incluido `pending` — reencolar no es rechazar. Antes el UC lo asignaba tal cual llegara, así que aprobar mandando motivo dejaba una fila que se contradice, y rechazar sin motivo dejaba al dueño sin saber qué corregir.

Va en el schema y no en el UC porque es validación de la forma del payload, y así la asignación incondicional de `verify.py` queda correcta por construcción. Un motivo en blanco cuenta como ausente: `StrictBase` tiene `str_strip_whitespace=True`, así que `"   "` llega como `""`.

### Aprobar exige dos saltos; el import ahora entra directo en `pending`

Desde `unverified` el único destino legal es `pending`, y recién desde ahí se puede `verified` o `rejected` — o sea que **ninguna propiedad se aprueba en una sola llamada**. En el diseño original ese primer salto lo dispara el dueño al pedir verificación.

Un import masivo no tiene dueño pidiendo nada, así que hasta el 2026-08-01 las filas importadas quedaban en `unverified`, fuera de toda cola (detectado el 2026-07-29 al estimar los botones de moderación). **Resuelto haciendo que el import escriba `pending` directo** ([seed_mapper.py:243](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py#L243)): el admin que sube el CSV *es* quien está pidiendo que se revise el lote, así que las filas nacen encoladas.

Es legal porque **nacer en un estado no es una transición**: el worker construye el modelo y hace `bulk_insert`, sin pasar nunca por `VerifyPropertyUseCase` ni por su `_ALLOWED_TRANSITIONS`.


### Publicar y verificar son ejes independientes, por decisión

Las dos state machines son separadas y **no** hay regla que ate publicar a estar verificado. Una propiedad puede estar visible *mientras* se revisa, avisándolo con un badge; acoplarlas sería una decisión de producto adicional, no una regla del dominio.

Por eso el import mantiene `status=ListingStatus.active` ([seed_mapper.py:236](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py#L236)) — que además pisa el default `draft` del modelo. La contracara es que el aviso hoy solo existe en el detalle público: `PropertyCardSchema` no lleva `verification_status`, así que el feed y el mapa no pueden mostrarlo (ver [[properties-service-search]]). Y mientras el 100% del inventario esté en `pending`, el badge no comunica nada: su valor depende de que la cola se trabaje, no de mostrarlo. Ver [[open-items]].

### El detalle admin está acoplado al público

`GET /admin/properties/{id}` devuelve el mismo `PropertyDetailSchema` que el endpoint público **y comparte la key `cache_property`**. Eso bloquea sumarle campos admin-only —documentos de verificación, `owner_id`, `rejection_reason`— sin partir antes el schema: agregarlos los publicaría en el endpoint público y envenenaría el cache compartido.

### Los tres endpoints de moderación devuelven 204 sin cuerpo

`PATCH /properties/{id}/status`, `PATCH /properties/{id}/verification` y `POST /properties/{id}/estimated-price` responden `204 NO CONTENT`. **Se decidió dejarlo así** (2026-08-02): el consumidor refetchea.

La alternativa —devolver la fila actualizada para que el cliente la parchee en memoria— se descartó porque con filtros activos el front tendría que decidir si la fila sigue matcheando y recalcular el `total`, o sea reimplementar en JavaScript el `WHERE` de `_apply_filters` del repo, en un segundo lugar que hay que mantener sincronizado. Ver [[frontend-admin-panel]].

Los dos de moderación **sí invalidan cache** tras escribir (`cache_property` y las keys derivadas), así que refetchear devuelve el estado nuevo. `set_estimated_price` **no toca cache** — probablemente correcto, porque `admin_estimated_price` no forma parte de `PropertyDetailSchema`, pero conviene confirmarlo al cablear esa acción.

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

> **Trazabilidad — se deriva, no se almacena.** `Property.bulk_job_id` se declaró en `f3a0c4d` y se **eliminó el 2026-07-27** sin haber llegado nunca a una migración: nadie la escribía, y con ids determinísticos el set de properties de un import se reconstruye desde el CSV (`uuid5` por `external_id`), que sigue en storage vía `bulk_jobs.storage_key`. Ver [[adr-bulk-idempotent-external-id]]. Costo asumido: no hay forma de consultar en SQL directo qué properties salieron de qué import.

## Listado admin (`GET /admin/properties`)

Devuelve `AdminPropertiesPage` — `{items, total, page, page_size}` — con filtros por `status`, `verification_status` y `owner_id`, todos como query params.

**Por qué no reusa `PropertyCardSchema`**: ese es el card *público*, el que consumen el feed y "mis propiedades", y esconde justo lo que la moderación necesita — `verification_status`, `owner_id`, `created_at`, `rejection_reason`. Antes el endpoint devolvía una lista pelada de ese schema, así que una tabla de moderación podía **filtrar por campos que no podía mostrar**, y paginar sin saber cuántas páginas hay. `AdminPropertyCardSchema` es nuevo y no hereda del público, para que un cambio del feed no arrastre al panel.

**Paginación por offset, no con el cursor opaco del feed** (ver [[adr-admin-offset-pagination]]).

Dos detalles de implementación que valen la pena:

- `get_all` y `count_all` comparten `_apply_filters`. Si cada uno armara su propio `WHERE`, agregar un filtro a uno y olvidarlo en el otro haría que el total mienta sin que nada falle.
- El `noload` sobre `images`, `location` y `promotions` no es una micro-optimización: `Property` las carga con `selectin`, así que cada página traía filas de imágenes, geometrías PostGIS y promociones que el schema admin descarta. Pasó de 5 queries por request a 2.
- La página y el conteo van **secuenciales, no con `asyncio.gather`**: comparten la `Session` del UoW y una `Session` de SQLAlchemy no es segura entre threads.

## Promociones

`promoted_listings` modela campañas con `starts_at`/`ends_at`/`priority`/`is_active`. `Property.promotions` es una relación **viewonly** filtrada por `is_active=True`, lo que alimenta `is_promoted` en `PropertyCardSchema`. Crear una promoción exige que la property esté `active` (`PropertyNotReadyForPromotionError`); no se permite más de una activa (`DuplicateActivePromotionError`).

## Claims

- `GET /admin/properties` devuelve `AdminPropertiesPage` con `items`, `total`, `page` y `page_size` ([admin.py](backend/properties-service/src/app/api/routes/admin.py), [admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- `AdminPropertyCardSchema` incluye `verification_status`, `owner_id`, `created_at` y `rejection_reason`, que `PropertyCardSchema` no expone ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- `get_all` y `count_all` comparten `_apply_filters`, y `get_all` aplica `noload` a `images`, `location` y `promotions` ([sql_property_repository.py](backend/properties-service/src/app/services/admin/adapters/sql_property_repository.py)).
- Las rutas `/admin/*` están protegidas con `dependencies=[Depends(require_admin)]` a nivel router ([admin.py:43-47](backend/properties-service/src/app/api/routes/admin.py#L43-L47)).
- `set_status` valida transiciones contra `_ALLOWED_TRANSITIONS` y lanza `InvalidStatusTransitionError` si no aplica ([set_status.py:39-44](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py#L39-L44)).
- `VerifyPropertyUseCase._ALLOWED_TRANSITIONS` mapea `unverified → [pending]`, `pending → [verified, rejected]`, `rejected → [pending]` y `verified → [pending, rejected]` ([verify.py:13-18](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py#L13-L18)).
- `VerifyPropertyUseCase.execute()` y `SetPropertyStatusUseCase.execute()` reciben `principal` y escriben `updated_by` ([verify.py](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py), [set_status.py](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py)).
- `VerifyPropertyUseCase` escribe `verified_by` cuando el target está en `_RESOLVED_STATES` (`verified`, `rejected`) y lo deja en `None` en cualquier otro caso ([verify.py](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py)).
- `VerifyPropertyRequest` declara un `model_validator(mode="after")` que exige `rejection_reason` si el target es `rejected` y lo rechaza si no lo es ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- Las rutas `PATCH /admin/properties/{id}/status` y `PATCH /admin/properties/{id}/verification` declaran `principal: Annotated[Principal, Depends(require_admin)]` ([admin.py](backend/properties-service/src/app/api/routes/admin.py)).
- Ninguna propiedad puede pasar de `unverified` a `verified` en una sola llamada: `pending` es paso obligatorio ([verify.py:13-18](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py#L13-L18)).
- El worker de import fija `status=ListingStatus.active` y `verification_status=VerificationStatus.pending` al construir cada `Property` ([seed_mapper.py:236,243](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py#L236-L243)).
- Construir un `Property` con un `verification_status` dado no pasa por `VerifyPropertyUseCase`, así que `_ALLOWED_TRANSITIONS` no aplica al estado inicial de una fila importada ([seed_mapper.py](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py), [verify.py](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py)).
- `GetPropertyDetailAdminUseCase` devuelve `PropertyDetailSchema` y usa la misma key `cache_property` que el `GetPropertyUseCase` público ([get_property_detail.py:25](backend/properties-service/src/app/services/admin/use_cases/get_property_detail.py#L25), [get_property.py:29](backend/properties-service/src/app/services/listing/use_cases/property_core/get_property.py#L29)).
- `GetPropertyDetailAdminUseCase` solo escribe al cache cuando `status == active`, así que borradores e inactivos se leen siempre desde la DB ([get_property_detail.py:46-54](backend/properties-service/src/app/services/admin/use_cases/get_property_detail.py#L46-L54)).
- `VerifyPropertyUseCase` y `SetPropertyStatusUseCase` borran `cache_property` tras escribir; `SetEstimatedPriceUseCase` no invalida cache ([verify.py:51](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py#L51), [set_status.py:55](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py#L55), [set_estimated_price.py](backend/properties-service/src/app/services/admin/use_cases/estimated_price/set_estimated_price.py)).
- `set_property_status`, `verify_property` y `set_estimated_price` declaran `status_code=status.HTTP_204_NO_CONTENT` — ninguno devuelve la entidad actualizada ([admin.py:156-190](backend/properties-service/src/app/api/routes/admin.py#L156-L190)).
- `InvalidStatusTransitionError` usa el código `INVALID_STATUS_TRANSITION` y lleva `{current, target}` en su contexto ([listing.py:159-165](backend/properties-service/src/app/core/exceptions/listing.py#L159-L165)).
- `SetEstimatedPriceUseCase` escribe `admin_estimated_price` si hay principal, `ml_estimated_price` si no ([set_estimated_price.py:26-32](backend/properties-service/src/app/services/admin/use_cases/estimated_price/set_estimated_price.py#L26-L32)).
- El path ML de `set_estimated_price` no tiene caller — `workers/` está vacío al 2026-05-28 ([workers/](backend/properties-service/src/app/workers)).
- `BulkCreatePropertiesUseCase` (`use_cases/bulk_create_properties.py`) solo encola: crea la fila en `bulk_jobs` y devuelve el `batch_id`; no procesa el CSV ([bulk_create_properties.py](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py)).
- Un retry hereda `expires_at` del job original en vez de recibir una ventana nueva, y se rechaza con `RetryOfRetryNotAllowedError` si el target ya es un retry o con `BulkJobExpiredError` si está vencido ([bulk_create_properties.py](backend/properties-service/src/app/services/admin/use_cases/bulk_create_properties.py)).
- `POST /admin/properties/bulk` responde `202` con `batch_id` y agenda el worker vía `BackgroundTasks`; el procesamiento no ocurre dentro del request ([admin.py](backend/properties-service/src/app/api/routes/admin.py)).
- `build_models()` recibe `owner_id` resuelto desde el `email` de la fila del CSV vía `email_cache`, y `created_by=principal.sub` — ya no son el mismo UUID ([orm_objects.py](backend/properties-service/src/app/workers/helpers/mapping/orm_objects.py), [seed_mapper.py](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py)).
- `Property` no tiene columna de vínculo a `BulkJob` — `bulk_job_id` se removió del modelo sin haberse migrado nunca ([listing.py](backend/properties-service/src/app/models/listing.py)).
- `Account` en users-service tiene `account_id` y `email` como únicos identificadores indexados/únicos — no existe ningún campo de documento de identidad (cédula) ([account.py:37-53](backend/users-service/src/app/models/account.py#L37-L53)).
- `Property.promotions` es una relación viewonly filtrada por `is_active=True` ([listing.py](backend/properties-service/src/app/models/listing.py)).
- `is_promoted` en `PropertyCardSchema` se calcula desde la presencia de promociones activas ([property_card.py:64-69](backend/properties-service/src/app/services/shared/schemas/property_card.py#L64-L69)).
