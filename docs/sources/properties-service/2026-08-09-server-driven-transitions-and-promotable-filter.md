---
title: Transiciones servidas por el backend y filtro de promocionables
captured-from: conversation
captured-on: 2026-08-09
participants: [author, claude]
---

## Context

El front duplicaba a mano las tablas de transiciones de moderación, con riesgo de
drift silencioso (open item conocido). Al cablear la tab de promociones apareció
el mismo patrón: la UI ofreciendo lo que el backend iba a rechazar.

## Key conclusions

- **Las máquinas de estado se unifican en
  `services/shared/helpers/status_transitions.py`**: `VERIFICATION_TRANSITIONS`,
  `LISTING_STATUS_TRANSITIONS` y `OWNER_VISIBILITY_TRANSITIONS`. Los use cases de
  moderación y `SetPropertyVisibilityUseCase` perdieron sus copias locales.
- **Van en `shared/` y no en un helper admin** porque si no `services/listing`
  terminaba importando de `services/admin`.
- **El detalle admin publica los destinos legales** vía
  `AdminPropertyDetailSchema`, que extiende `PropertyDetailSchema` con
  `allowed_verification_targets` y `allowed_status_targets` requeridos.
- **Son derivados, así que se calculan a la salida** (`_with_transitions`), en el
  camino de cache y en el de DB: no se guardan ni se cachean, y la entrada bajo
  `cache_property` sigue siendo la misma que sirve al detalle público.
- **Se descartó meterlos en el payload cacheado.** Funcionaría —el schema público
  declara `extra="ignore"` y descartaría lo de más— pero quien escribe primero
  fija la forma, y un campo derivado no necesita cachearse.
- **`GET /admin/properties` acepta `is_promoted`**, implementado como `EXISTS`
  correlacionado y no como join: con join una property con varias promociones
  duplicaría filas y `count_all` dejaría de coincidir con las filas devueltas.
- **La condición del filtro es solo `is_active`**, igual que
  `get_active_by_property_id` — es la que decide el
  `DuplicateActivePromotionError`, no la de "se ve en el feed" (no mira
  `ends_at`).
- **El criterio de fondo**: cada regla que el backend valida al escribir debe
  poder consultarse antes de escribir, o la UI ofrece cosas que van a fallar.
  Vale para las transiciones y para las dos condiciones de promocionable
  (`status=active`, sin promoción activa).

## Open questions

- `GetPropertyDetailAdminUseCase` y `_with_transitions` no tienen test propio; se
  verificaron a mano contra un payload real.
- La máquina del dueño y la de admin comparten archivo pero no reglas: el dueño
  solo hace `draft ↔ active` y nada lo saca de `inactive`/`sold`/`rented`. Queda
  documentado, no unificado.

## Next steps

- Cubrir con tests el detalle admin y el cálculo de destinos.
- Al exponer prioridad y vencimiento de promociones, evaluar un schema propio en
  vez de `PropertyCardSchema`.
