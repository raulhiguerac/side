---
title: La tab de promociones cableada, y el pie del panel como slot
captured-from: conversation
captured-on: 2026-08-09
participants: [author, claude]
---

## Context

Continuación del mismo día: el armazón de promociones estaba montado sin datos, y
el panel de vista previa traía el formulario de moderación fijo adentro — que en
las vistas de promociones habría aparecido con un "Guardar" muerto.

## Key conclusions

- **El pie del panel es un slot.** `AdminPropertyPreviewPanel` expone
  `#footer` con la property ya cargada como slot prop, y perdió las props de
  guardado y el emit `save`. Cada tab pone el suyo: moderación su formulario,
  promociones el de crear o el de quitar. La vista de moderación se ahorró el
  reenvío de dos saltos que había antes (form → panel → vista).
- **Promocionar**: `AdminPromotionForm` con chips 7/15/30 más campo libre
  acotado a 1–60, prioridad como dropdown 1–5, y la fecha de vencimiento
  calculada en el cliente debajo de la duración —`promoted_days` es un número
  abstracto, la fecha es lo que se quiere saber—. Emite `{ promotedDays,
  priority }`; el `property_id` lo pone la vista desde el slot prop.
- **`usePromoteProperty` puede decir qué falló**, a diferencia de moderar: los
  dos 409 (`DUPLICATE_ACTIVE_PROMOTION`, `PROPERTY_NOT_READY_FOR_PROMOTION`)
  llegan distinguidos por `code`, que el handler del backend sí conserva.
- **Tras promocionar no se refresca el panel**, solo la lista:
  `PropertyDetailSchema` no lleva `is_promoted`, así que nada de lo que se está
  mirando cambió, y la fila sale sola del listado por dejar de cumplir
  `is_promoted: false`.
- **Quitar**: el botón del pie solo abre `RemovePromotionModal`; el botón que
  dispara el DELETE está en el modal. El modal es presentacional —emite
  `confirm`/`close` y no hace el request—, a diferencia de
  `DeletePropertyModal`, que se autogestiona y reporta con `alert()`. Se cierra
  pase lo que pase y el error queda en el pie, que es donde el admin sigue
  mirando.
- **`remove()` vive dentro de `useActivePromotions`** y no en un composable
  aparte: acá el dueño de la lista y el de la acción son el mismo, y tras el
  DELETE hay que releerla igual.
- **`useActivePromotions` pagina contra el servidor sin acumular páginas en
  memoria** — a diferencia de `useAdminProperties`, que usa `usePagination`.
  Quitar una promoción corre a todas las siguientes, así que una copia local
  quedaría desalineada al primer borrado.
- **`useRowSelection` acepta un extractor de clave.** El listado de promociones
  lista promociones, pero el panel necesita el `property_id`.
- **La tabla de activas muestra prioridad y vencimiento** con los días restantes
  calculados ("en 5 días", "vence hoy", "vencida"): la fecha sola obliga a hacer
  la cuenta mentalmente.

## Open questions

- El flujo no se probó contra el backend real; la verificación fue build,
  typecheck y tests.
- Cada cambio de contrato del backend rompió el front en runtime primero (props
  `allowed_*` sin default contra un backend viejo, y la respuesta del listado de
  promociones cambiando de array a página). Los tipos se escriben a mano en los
  dos lados.

## Next steps

- Correr la tab contra el 8003 reiniciado.
- Generar los tipos del front desde el OpenAPI del backend, que es la clase de
  bug que apareció dos veces en el día.
