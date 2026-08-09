---
title: Dominio admin — properties-service
status: draft
last-verified: 2026-08-09
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[properties-service-architecture]]"
  - "[[adr-estimated-price-dual-signal]]"
  - "[[adr-bulk-idempotent-external-id]]"
  - "[[adr-admin-offset-pagination]]"
  - "[[adr-verification-reversible-lifecycle]]"
  - "[[adr-transitions-served-by-backend]]"
  - "[[analytics-service]]"
  - "[[frontend-admin-panel]]"
  - "[[open-items]]"
  - "[[properties-service-bulk-create-worker]]"
  - "[[properties-service-users]]"
  - "[[properties-service-search]]"
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md, ../../../sources/properties-service/2026-07-16-bulk-create-sync-timeout-risk.md, ../../../sources/properties-service/2026-07-16-bulk-create-owner-id-resolution.md, ../../../sources/properties-service/2026-07-19-bulk-create-worker-streaming-csv.md, ../../../sources/properties-service/2026-07-27-bulk-async-import-worker.md, ../../../sources/properties-service/2026-07-28-bulk-import-smoke-test.md, ../../../sources/properties-service/2026-07-29-moderation-state-machines-block-imports.md, ../../../sources/properties-service/2026-08-01-bulk-import-pending-verification.md, ../../../sources/properties-service/2026-08-02-moderation-lifecycle-verified-not-terminal.md, ../../../sources/properties-service/2026-08-09-server-driven-transitions-and-promotable-filter.md, ../../../sources/properties-service/2026-08-09-promotions-schema-pagination-and-expiry-filter.md]
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
| `ListAllPromotionsUseCase` | `use_cases/promotions/list_all.py` | Listado admin de promociones vigentes, paginado por offset y sin cache. |
| `RequestBulkUploadUrlUseCase` | `use_cases/request_bulk_upload_url.py` | Emite la presigned PUT para subir el CSV a MinIO; no persiste nada. |
| `BulkCreatePropertiesUseCase` | `use_cases/bulk_create_properties.py` | **Solo encola**: valida el retry, crea la fila en `bulk_jobs`, devuelve `batch_id`. |
| `GetBulkJobStatusUseCase` | `use_cases/get_bulk_job_status.py` | Status + errores del job; marca `failed` los `pending` vencidos. |

## State machine de status

`set_status` solo permite transiciones declaradas en `LISTING_STATUS_TRANSITIONS` ([status_transitions.py](backend/properties-service/src/app/services/shared/helpers/status_transitions.py)):

| Desde | Hacia |
|---|---|
| `draft` | `active` |
| `active` | `draft`, `inactive`, `sold`, `rented` |
| `inactive` | `active`, `draft` |
| `sold` | `inactive` |
| `rented` | `inactive` |

Una transición no permitida lanza `InvalidStatusTransitionError`. Tras el cambio se invalida cache de detalle, mis-propiedades del owner y celdas H3 (para que el feed-mapa refleje el cambio de visibilidad).

### State machine de `verification_status` (independiente de la de arriba)

`VerifyPropertyUseCase` valida contra `VERIFICATION_TRANSITIONS`, una tabla **separada** de la de `ListingStatus` de arriba aunque viva en el mismo módulo:

| Desde | Hacia |
|---|---|
| `unverified` | `pending` |
| `pending` | `verified`, `rejected` |
| `rejected` | `pending` |
| `verified` | `pending`, `rejected` |

Una transición no permitida lanza el mismo `InvalidStatusTransitionError` que `set_status`.

**`verified` no es terminal** (desde el 2026-08-02, ver [[adr-verification-reversible-lifecycle]]): una property aprobada que después viola las normas se revoca a `rejected`, y un cambio de fotos la devuelve a `pending`. Lo único prohibido desde ahí es volver a `unverified`, que existe solo como estado inicial y al que no apunta ninguna transición.

Dar de baja una publicación **no** vive en este eje: es `status: active → inactive`, y funciona como takedown real porque la máquina del dueño solo hace `draft ↔ active` (ver [[properties-service-listing]]).

### Las tres máquinas viven en un módulo compartido, y el detalle las publica

Desde el 2026-08-09 las tablas no son privadas de sus use cases: `VERIFICATION_TRANSITIONS`, `LISTING_STATUS_TRANSITIONS` y la del dueño (`OWNER_VISIBILITY_TRANSITIONS`, ver [[properties-service-listing]]) están en [status_transitions.py](backend/properties-service/src/app/services/shared/helpers/status_transitions.py). Van en `services/shared/` y no en un helper admin porque `services/listing` consume la del dueño, y alojarla bajo `admin/` invertiría la dependencia entre dominios.

`GET /admin/properties/{id}` devuelve `AdminPropertyDetailSchema` — el detalle más `allowed_verification_targets` y `allowed_status_targets`, los destinos legales desde el estado en que está la property. Son **derivados** de `status`/`verification_status`, así que `_with_transitions` los calcula a la salida en los dos caminos (cache y DB) en vez de guardarlos: lo que se escribe al cache sigue siendo el `PropertyDetailSchema` pelado, la misma entrada que sirve al detalle público.

El motivo es que la UI no pueda ofrecer lo que el backend va a rechazar. Antes el front duplicaba las dos tablas a mano y el drift era silencioso; hoy ofrece exactamente lo que el use case acepta, porque sale del mismo dict. Ver [[adr-transitions-served-by-backend]] y [[frontend-admin-panel]].

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

### El detalle admin ya tiene schema propio, pero sigue compartiendo la cache key

Hasta el 2026-08-09 devolvía el mismo `PropertyDetailSchema` que el endpoint público. Ahora devuelve `AdminPropertyDetailSchema`, que lo extiende — así que **un campo admin-only derivado ya no está bloqueado**: se calcula a la salida y nunca toca el cache.

Lo que sigue compartido es la key `cache_property`. Para campos admin-only **almacenados** —documentos de verificación, el precio estimado— el bloqueo persiste: escribirlos en esa entrada los expondría al detalle público. Las salidas serían una key propia para el detalle admin, o guardar el superset y dejar que cada schema descarte lo que no le corresponde (`PropertyDetailSchema` declara `extra="ignore"`), con el riesgo de que quien escriba primero fije la forma. Ver [[open-items]].

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

Devuelve `AdminPropertiesPage` — `{items, total, page, page_size}` — con filtros por `status`, `verification_status`, `owner_id` e `is_promoted`, todos como query params.

**Por qué no reusa `PropertyCardSchema`**: ese es el card *público*, el que consumen el feed y "mis propiedades", y esconde justo lo que la moderación necesita — `verification_status`, `owner_id`, `created_at`, `rejection_reason`. Antes el endpoint devolvía una lista pelada de ese schema, así que una tabla de moderación podía **filtrar por campos que no podía mostrar**, y paginar sin saber cuántas páginas hay. `AdminPropertyCardSchema` es nuevo y no hereda del público, para que un cambio del feed no arrastre al panel.

**Paginación por offset, no con el cursor opaco del feed** (ver [[adr-admin-offset-pagination]]).

Dos detalles de implementación que valen la pena:

- `get_all` y `count_all` comparten `_apply_filters`. Si cada uno armara su propio `WHERE`, agregar un filtro a uno y olvidarlo en el otro haría que el total mienta sin que nada falle.
- El `noload` sobre `images`, `location` y `promotions` no es una micro-optimización: `Property` las carga con `selectin`, así que cada página traía filas de imágenes, geometrías PostGIS y promociones que el schema admin descarta. Pasó de 5 queries por request a 2.
- La página y el conteo van **secuenciales, no con `asyncio.gather`**: comparten la `Session` del UoW y una `Session` de SQLAlchemy no es segura entre threads.

`is_promoted` (agregado el 2026-08-09) filtra por promoción activa con un **`EXISTS` correlacionado, no un join**: con join una property con varias promociones duplicaría filas y `count_all` dejaría de coincidir con las filas devueltas. Su condición es solo `is_active`, la misma que usa `get_active_by_property_id` — o sea la que decide el `DuplicateActivePromotionError`, sin mirar `ends_at`. Con `status=active` cubre las dos reglas que valida `CreatePromotionUseCase`, así que un cliente puede listar exactamente lo promocionable en vez de ofrecer y fallar.

## Promociones

`promoted_listings` modela campañas con `starts_at`/`ends_at`/`priority`/`is_active`. Crear una promoción exige que la property esté `active` (`PropertyNotReadyForPromotionError`) y que no tenga otra vigente (`DuplicateActivePromotionError`); `promoted_days` acepta entre 1 y 60 — el tope es de producto, una promoción es una campaña y no un estado permanente. Las dos condiciones son consultables antes de escribir vía los filtros `status` e `is_promoted` del listado admin (ver [[adr-transitions-served-by-backend]]).

### "Vigente" se define una sola vez (2026-08-09)

Nada apaga `is_active` al llegar `ends_at`: sin un job que expire las vencidas, una campaña terminada seguía contando como ad pago y como "promocionada". Hasta que ese job exista, la fecha se filtra **en cada lectura** con `active_promotion_clause()` ([promotion.py](backend/properties-service/src/app/models/promotion.py)) — `is_active AND ends_at > now()`.

Se define una sola vez a propósito, mismo criterio que las transiciones: una lectura que se olvide del `ends_at` deja volver la promoción vencida por ese camino y por ninguno otro. La usan las cinco consultas que deciden vigencia —listado admin, su `count`, el guard de duplicados, el filtro `is_promoted` y el join de ads del feed— más la relación `Property.promotions`, que la necesita **como string** porque el `primaryjoin` se evalúa recién en `configure_mappers()`. Esa relación es la que alimenta `is_promoted` en `PropertyCardSchema`.

Es `func.now()` y no `datetime.now()`: se resuelve en Postgres al correr la query, mientras que la versión Python quedaría congelada en el import del módulo. El predicado vive en `models/` y no en `services/shared/helpers/` porque un modelo importando de servicios invierte la dependencia.

Efecto colateral asumido: como el guard de duplicados también filtra por fecha, una promoción vencida **ya no se puede quitar** con el DELETE (404), y la fila queda `is_active=True` invisible hasta que exista el job. Ver [[open-items]].

### El listado tiene schema propio, pagina y no cachea (2026-08-09)

`GET /admin/promotions` devuelve `AdminPromotionsPage` con `AdminPromotionSchema` —`id`, `property_id`, `priority`, `starts_at`, `ends_at`, `is_active` y la card de la property anidada—. Antes devolvía `list[PropertyCardSchema]`, que solo sabe responder "¿está promocionada?": una tabla de promociones no podía mostrar prioridad ni vencimiento, que es lo único que la promoción decide.

**Dejó de cachear.** Leía y escribía `feed_ads_global()`, la key de ads del feed público, así que cambiarle la forma a la respuesta la habría envenenado para todos los lectores del feed — el mismo bug que tenía el endpoint borrado, sobre una key más caliente. Es una lectura interna y de pocas filas: no amerita cache propia.

**Pagina por offset** (mismo criterio que [[adr-admin-offset-pagination]]), ordenado por `priority desc, ends_at asc, id`. El `id` desempata: sin orden total, dos promociones con igual prioridad y fecha pueden intercambiarse entre queries y el offset repetiría o saltearía filas.

### `GET /admin/properties/{id}/promotions` se borró (2026-08-09)

Devolvía una lista de un solo elemento con la card de la property, nunca las promociones — o sea la misma respuesta que ya da `is_promoted`. No tenía consumidores y leía/escribía `cache_property` con el schema equivocado: cualquier llamada desde `/docs` envenenaba el cache del detalle público. Se borró la ruta, el UC, su dependencia y `get_all_by_property_id`, su único caller. El historial de promociones de una property, si alguna vez hace falta, es otro endpoint: `list[PromotionSchema]` incluyendo las inactivas.

## Claims

- `GET /admin/properties` devuelve `AdminPropertiesPage` con `items`, `total`, `page` y `page_size` ([admin.py](backend/properties-service/src/app/api/routes/admin.py), [admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- `AdminPropertyCardSchema` incluye `verification_status`, `owner_id`, `created_at` y `rejection_reason`, que `PropertyCardSchema` no expone ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- `get_all` y `count_all` comparten `_apply_filters`, y `get_all` aplica `noload` a `images`, `location` y `promotions` ([sql_property_repository.py](backend/properties-service/src/app/services/admin/adapters/sql_property_repository.py)).
- Las rutas `/admin/*` están protegidas con `dependencies=[Depends(require_admin)]` a nivel router ([admin.py:43-47](backend/properties-service/src/app/api/routes/admin.py#L43-L47)).
- `set_status` valida transiciones contra `LISTING_STATUS_TRANSITIONS` y lanza `InvalidStatusTransitionError` si no aplica ([set_status.py](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py), [status_transitions.py](backend/properties-service/src/app/services/shared/helpers/status_transitions.py)).
- `VERIFICATION_TRANSITIONS` mapea `unverified → [pending]`, `pending → [verified, rejected]`, `rejected → [pending]` y `verified → [pending, rejected]` ([status_transitions.py](backend/properties-service/src/app/services/shared/helpers/status_transitions.py)).
- Ni `verify.py` ni `set_status.py` declaran tablas de transiciones propias: las importan del módulo compartido ([verify.py](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py), [set_status.py](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py)).
- `VerifyPropertyUseCase.execute()` y `SetPropertyStatusUseCase.execute()` reciben `principal` y escriben `updated_by` ([verify.py](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py), [set_status.py](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py)).
- `VerifyPropertyUseCase` escribe `verified_by` cuando el target está en `_RESOLVED_STATES` (`verified`, `rejected`) y lo deja en `None` en cualquier otro caso ([verify.py](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py)).
- `VerifyPropertyRequest` declara un `model_validator(mode="after")` que exige `rejection_reason` si el target es `rejected` y lo rechaza si no lo es ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- Las rutas `PATCH /admin/properties/{id}/status` y `PATCH /admin/properties/{id}/verification` declaran `principal: Annotated[Principal, Depends(require_admin)]` ([admin.py](backend/properties-service/src/app/api/routes/admin.py)).
- Ninguna propiedad puede pasar de `unverified` a `verified` en una sola llamada: `pending` es paso obligatorio ([status_transitions.py](backend/properties-service/src/app/services/shared/helpers/status_transitions.py)).
- El worker de import fija `status=ListingStatus.active` y `verification_status=VerificationStatus.pending` al construir cada `Property` ([seed_mapper.py:236,243](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py#L236-L243)).
- Construir un `Property` con un `verification_status` dado no pasa por `VerifyPropertyUseCase`, así que `_ALLOWED_TRANSITIONS` no aplica al estado inicial de una fila importada ([seed_mapper.py](backend/properties-service/src/app/workers/helpers/mapping/seed_mapper.py), [verify.py](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py)).
- `GetPropertyDetailAdminUseCase` devuelve `AdminPropertyDetailSchema` y usa la misma key `cache_property` que el `GetPropertyUseCase` público ([get_property_detail.py](backend/properties-service/src/app/services/admin/use_cases/get_property_detail.py), [get_property.py:29](backend/properties-service/src/app/services/listing/use_cases/property_core/get_property.py#L29)).
- `AdminPropertyDetailSchema` declara `allowed_verification_targets` y `allowed_status_targets` como requeridos, y `_with_transitions` los puebla desde el módulo compartido ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py), [get_property_detail.py](backend/properties-service/src/app/services/admin/use_cases/get_property_detail.py)).
- Lo que `GetPropertyDetailAdminUseCase` escribe al cache es un `PropertyDetailSchema`, sin los campos derivados ([get_property_detail.py](backend/properties-service/src/app/services/admin/use_cases/get_property_detail.py)).
- `GetPropertiesAdminRequest` acepta `is_promoted` y `_apply_filters` lo traduce a un `EXISTS` correlacionado sobre `PromotedListing` filtrado por `active_promotion_clause()` ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py), [sql_property_repository.py](backend/properties-service/src/app/services/admin/adapters/sql_property_repository.py)).
- `GetPropertyDetailAdminUseCase` solo escribe al cache cuando `status == active`, así que borradores e inactivos se leen siempre desde la DB ([get_property_detail.py:46-54](backend/properties-service/src/app/services/admin/use_cases/get_property_detail.py#L46-L54)).
- `SetPropertyStatusUseCase` borra `feed_ads_global()` y `feed_ads_by_city()` además de `cache_property`, sin consultar antes si la property estaba promocionada ([set_status.py](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py)).
- `active_promotion_clause()` está definido en `models/promotion.py` y lo usan el repo de promociones, el filtro `is_promoted` del repo admin y el join de ads del feed ([promotion.py](backend/properties-service/src/app/models/promotion.py), [sql_promotion_repository.py](backend/properties-service/src/app/services/admin/adapters/sql_promotion_repository.py), [sql_property_repository.py](backend/properties-service/src/app/services/admin/adapters/sql_property_repository.py), [sql_property_search_repository.py](backend/properties-service/src/app/services/search/adapters/sql_property_search_repository.py)).
- `GET /admin/promotions` devuelve `AdminPromotionsPage` y `ListAllPromotionsUseCase` no recibe `CachePort` ([admin.py](backend/properties-service/src/app/api/routes/admin.py), [list_all.py](backend/properties-service/src/app/services/admin/use_cases/promotions/list_all.py)).
- `CreatePromotionRequest.promoted_days` declara `ge=1, le=60` ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- No existe ninguna ruta `GET /admin/properties/{property_id}/promotions` ni el use case que la servía ([admin.py](backend/properties-service/src/app/api/routes/admin.py), [use_cases/promotions/](backend/properties-service/src/app/services/admin/use_cases/promotions)).
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
- `Property.promotions` es una relación viewonly cuyo `primaryjoin` filtra `is_active` **y** `ends_at > now()` ([listing.py](backend/properties-service/src/app/models/listing.py), [promotion.py](backend/properties-service/src/app/models/promotion.py)).
- `is_promoted` en `PropertyCardSchema` se calcula desde la presencia de promociones activas ([property_card.py:64-69](backend/properties-service/src/app/services/shared/schemas/property_card.py#L64-L69)).
