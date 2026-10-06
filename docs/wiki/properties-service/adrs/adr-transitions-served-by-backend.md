---
title: ADR-0011 — Las transiciones legales las sirve el backend, no las duplica el cliente
status: stable
last-verified: 2026-08-09
owners: [properties-service]
related:
  - "[[properties-service-admin]]"
  - "[[properties-service-listing]]"
  - "[[adr-verification-reversible-lifecycle]]"
  - "[[frontend-admin-panel]]"
  - "[[open-items]]"
sources: [../../../sources/properties-service/2026-08-09-server-driven-transitions-and-promotable-filter.md]
---

# ADR-0011 — Las transiciones legales las sirve el backend, no las duplica el cliente

## Contexto

Las dos máquinas de estado de moderación vivían como `_ALLOWED_TRANSITIONS`
privadas dentro de sus use cases, sin exponerse por API. El panel admin del
frontend necesitaba saber qué transiciones ofrecer para cada fila, así que
copió las dos tablas a mano en `constants/moderationTransitions.ts`.

Esa copia solo podía fallar en silencio: un cambio en `verify.py` o
`set_status.py` dejaba al front ofreciendo transiciones que vuelven `409
INVALID_STATUS_TRANSITION`, o escondiendo transiciones que ya eran legales.
Nada en el pipeline detecta la divergencia, porque son dos archivos que no se
referencian entre sí.

El mismo patrón reapareció al construir la tab de promociones: la UI tenía que
decidir qué properties son promocionables, y esa regla también vivía solo dentro
del use case que la valida al escribir.

## Decisión

**Cada regla que el backend valida al escribir se puede consultar antes de
escribir.**

1. Las tres máquinas de estado se unifican en
   [status_transitions.py](backend/properties-service/src/app/services/shared/helpers/status_transitions.py):
   `VERIFICATION_TRANSITIONS`, `LISTING_STATUS_TRANSITIONS` y
   `OWNER_VISIBILITY_TRANSITIONS`. Los use cases de moderación y
   `SetPropertyVisibilityUseCase` importan de ahí en vez de declarar la suya.
2. El detalle admin publica los destinos legales del estado actual vía
   `AdminPropertyDetailSchema`, que extiende `PropertyDetailSchema` con
   `allowed_verification_targets` y `allowed_status_targets`.
3. `GET /admin/properties` acepta `is_promoted`, que junto con `status` cubre las
   dos condiciones que valida `CreatePromotionUseCase`.
4. El cliente deja de tener tabla propia: el front borró
   `constants/moderationTransitions.ts` y el formulario recibe los destinos como
   prop (ver [[frontend-admin-panel]]).

Va en `services/shared/helpers/` y no en un helper del dominio admin porque
`services/listing` también consume la tabla del dueño: alojarla en `admin/`
haría que `listing` importara de `admin`, invirtiendo la dependencia entre
dominios.

## Alternativas consideradas

- **Test de contrato en CI** que compare la tabla del backend contra la del
  front. Es monorepo, así que era viable y barato, pero solo *detecta* el drift
  en vez de eliminarlo, y deja la duplicación viva.
- **Endpoint de metadata** (`GET /admin/moderation/transitions`) con las máquinas
  completas. Una sola fuente y un solo fetch, pero no soporta reglas
  condicionales al estado de la property ("no publicar sin fotos"), que es
  justamente hacia donde tiende la moderación.
- **Persistir los destinos en el payload cacheado.** Funcionaría —el schema
  público declara `extra="ignore"` y descartaría los campos de más— pero quien
  escribe primero fija la forma del cache, y un campo derivado no necesita
  cachearse.

## Consecuencias

- Los destinos se calculan a la salida (`_with_transitions`), en el camino de
  cache y en el de DB. **La cache no cambia**: se sigue guardando el
  `PropertyDetailSchema` pelado bajo `cache_property`, la misma entrada que sirve
  al detalle público.
- El detalle admin deja de compartir schema con el público. Lo que sigue
  compartido es la key de cache, que es el bloqueo restante para exponer campos
  admin-only **almacenados** —como el precio estimado— no derivados.
- El filtro `is_promoted` usa un `EXISTS` correlacionado y no un join: con join
  una property con varias promociones duplicaría filas y `count_all` dejaría de
  coincidir con las filas devueltas.
- La condición de ese filtro es solo `is_active`, igual que
  `get_active_by_property_id` — es la que decide el `DuplicateActivePromotionError`,
  no la de "se ve en el feed" (no mira `ends_at`).
- Front y backend se despliegan por separado, así que el cliente tiene que
  tolerar respuestas sin los campos nuevos: si llegan ausentes, el formulario no
  ofrece destinos en vez de romperse.

## Claims

- `VERIFICATION_TRANSITIONS`, `LISTING_STATUS_TRANSITIONS` y `OWNER_VISIBILITY_TRANSITIONS` viven en un único módulo compartido ([status_transitions.py](backend/properties-service/src/app/services/shared/helpers/status_transitions.py)).
- `VerifyPropertyUseCase`, `SetPropertyStatusUseCase` y `SetPropertyVisibilityUseCase` importan sus transiciones de ese módulo y no declaran tablas propias ([verify.py](backend/properties-service/src/app/services/admin/use_cases/moderation/verify.py), [set_status.py](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py), [set_property_visibility.py](backend/properties-service/src/app/services/listing/use_cases/property_core/set_property_visibility.py)).
- `AdminPropertyDetailSchema` extiende `PropertyDetailSchema` con `allowed_verification_targets` y `allowed_status_targets`, ambos requeridos ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
- `_with_transitions` construye el schema admin a la salida y `GetPropertyDetailAdminUseCase` lo aplica tanto al leer de cache como de DB ([get_property_detail.py](backend/properties-service/src/app/services/admin/use_cases/get_property_detail.py)).
- El valor escrito al cache sigue siendo un `PropertyDetailSchema` sin los campos derivados ([get_property_detail.py](backend/properties-service/src/app/services/admin/use_cases/get_property_detail.py)).
- El frontend no contiene ninguna tabla de transiciones: `constants/moderationTransitions.ts` fue eliminado ([frontend/src/constants](frontend/src/constants)).
