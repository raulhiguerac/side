---
title: "ADR-0011 — Promocionar vive en su propia sub-tab, no en el panel de moderación"
status: stable
last-verified: 2026-08-09
owners: [frontend]
related:
  - "[[frontend-admin-panel]]"
  - "[[adr-admin-tabs-nested-routes]]"
  - "[[adr-moderation-panel-staged-form]]"
  - "[[adr-transitions-served-by-backend]]"
  - "[[properties-service-admin]]"
sources: [../../../sources/frontend/2026-08-09-moderation-wiring-and-promotions-shell.md, ../../../sources/frontend/2026-08-09-promotions-tab-wired.md]
decision-date: 2026-08-09
decision-status: accepted
---

# ADR-0011 — Promocionar vive en su propia sub-tab, no en el panel de moderación

## Contexto

Los cuatro endpoints de promociones no incluyen ninguno que liste properties
*promocionables*: `GET /admin/promotions` devuelve las que ya lo están. Para
crear una promoción hay que elegir una property de algún otro lado, y el único
listado que existe es `GET /admin/properties`, el de moderación.

O sea que la tab de promociones tenía que resolver dos listados distintos —las
activas y las elegibles— con un solo lugar donde ponerlos.

## Decisión

Promociones se parte en dos sub-rutas bajo `/admin/properties/promotions`:
`""` (**Activas**, revisar y quitar) y `new` (**Promocionar**, elegir y crear).
Cada una con su tabla y el mismo panel de vista previa, aplicando el mismo
mecanismo que [[adr-admin-tabs-nested-routes]] un nivel más abajo.

La tab **Promocionar** no tiene listado propio: reusa `useAdminProperties` y
`AdminPropertiesTable` con `{ status: "active", is_promoted: false }`, que son
exactamente las dos condiciones que valida `CreatePromotionUseCase` (ver
[[adr-transitions-served-by-backend]]).

## Alternativas consideradas

- **Promocionar desde el panel de moderación.** Habría dejado la tab de
  promociones como solo-lectura, que era atractivo por lo barato. Descartado por
  dos razones: son dos trabajos distintos —control de políticas vs. vender
  ubicación en el feed—, y el panel tendría que cargar estado comercial (si ya
  existe una promoción activa) solo para decidir si pintar el botón. El día que
  exista un rol que solo modere, la acción de pago viajaría de contrabando.
- **Un modal con el listado de elegibles.** Descartado porque las dos sub-tabs
  necesitan el mismo dato de fondo y un modal lo re-pediría en cada apertura,
  además de no ser linkeable.
- **Buscador por id.** Los ids son UUID: nadie los tiene a mano. Si hace falta
  buscar, el listado admin ya acepta `owner_id`, que es el filtro con sentido
  operativo.

## Consecuencias

- La tab Activas queda como "ver y quitar"; crear es siempre un flujo aparte con
  su propia URL.
- La regla de negocio no se reimplementa en el cliente: si el backend cambia qué
  es promocionable, cambia el filtro, no la UI.
- Las columnas que dan sentido a Activas —prioridad y vencimiento— no existían en
  `PropertyCardSchema`, así que el backend expuso `AdminPromotionSchema` el mismo
  día (ver [[properties-service-admin]]); la tabla lista promociones, no
  properties, y se selecciona por `property_id` porque es lo que el panel pide.

## Claims

- Las promociones son una ruta padre con dos hijas: `""` (`admin-properties-promotions`) y `new` (`admin-properties-promotions-new`) ([router/routes/admin/properties.ts](frontend/src/router/routes/admin/properties.ts)).
- `AdminPromotionsCreateView.vue` llama `load({ status: "active", is_promoted: false })` y reusa `AdminPropertiesTable` ([AdminPromotionsCreateView.vue](frontend/src/views/admin/properties/promotions/AdminPromotionsCreateView.vue)).
- `AdminPromotionsActiveView.vue` usa `AdminPromotionsTable`, cuyas filas son `AdminPromotionRow` —la promoción con la property anidada— ([AdminPromotionsActiveView.vue](frontend/src/views/admin/properties/promotions/AdminPromotionsActiveView.vue), [AdminPromotionsTable.vue](frontend/src/components/admin/properties/promotions/AdminPromotionsTable.vue)).
- Ningún componente de moderación referencia promociones ([components/admin/properties/moderation/](frontend/src/components/admin/properties/moderation)).
