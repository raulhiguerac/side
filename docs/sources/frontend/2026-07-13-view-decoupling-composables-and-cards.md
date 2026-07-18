---
title: Patrón de desacople para views bloated (composables + tarjetas presentacionales)
captured-from: conversation
captured-on: 2026-07-13
participants: [raul, claude]
---

## Context

`MyPropertiesView.vue` y `EditPropertyView.vue` crecieron rápido durante el desarrollo del ciclo de vida de propiedades (borrar, toggle de visibilidad, formulario de edición con fotos/stats/info fija/detalles). Ambas veces se llegó al mismo diagnóstico: casi no hay lógica real (fetch + armar objeto + llamar endpoint), pero el archivo es enorme por el markup de UI. Se estableció y repitió el mismo patrón de refactor dos veces en la misma sesión.

## Key conclusions

- **Principio**: una view debe quedar solo con **orquestación** (qué mostrar, en qué orden, a qué endpoint llamar) — no con el markup de cada sección ni con el detalle de cómo hablarle a cada endpoint.
- **Regla de separación de dominios**: acciones de ciclo de vida distintas (borrar, cambiar visibilidad) no deben compartir estado ni lógica en la view aunque ambas sean "acciones sobre una propiedad" — son dominios distintos con distinto endpoint y distinto ciclo de vida de UI.
- **Patrón para acciones con confirmación/modal** (ej. borrar): componente autocontenido que envuelve `BaseModal.vue`, recibe el id como prop (`propertyId: string | null`, abierto ⟺ no-null), emite `close`/`deleted`, y hace la llamada HTTP + maneja su propio loading internamente. Ejemplo: `DeletePropertyModal.vue`.
- **Patrón para acciones sin UI propia** (ej. toggle de visibilidad): composable de una sola función que envuelve la llamada HTTP + try/catch, devuelve `boolean` de éxito — sin mutar estado ajeno. Ejemplo: `usePropertyVisibility.ts` (`toggleVisibility(id): Promise<boolean>`). La view mantiene la responsabilidad de actualizar su propia lista local tras el éxito, porque es la única que conoce esa lista.
- **Patrón para fetch + estado de una entidad**: composable que junta el `ref` de datos + `isLoading` + la función de fetch (mismo molde que `useFeed.ts` ya usaba). Ejemplo: `useMyProperties.ts` → `{ properties, isLoading, fetchProperties }`.
- **Patrón para forms editables reutilizando la convención del create flow**: los steps de creación (`StepTipo.vue`, `StepDetalles.vue`) ya usaban `:form="form"` + `@update:form="form = $event"` (reemplazo del objeto completo, no v-model por campo). Se reusó el mismo contrato para el form de edición (`PropertyEditForm.vue`), evitando inventar una API nueva.
- **Split de `EditPropertyView.vue` (437 → 96 líneas)** en 5 componentes bajo `components/properties/edit/`: `PropertyHeaderCard` (tipo/negocio/badge/ubicación/stats), `PropertyPhotosCard` (fotos, wrapea `PropertyPhotoGrid` compartido), `PropertyInfoCard` (chips fijos), `PropertyEditForm` (campos editables, absorbe el manejo de inputs de dinero formateado), `PropertyEditActions` (volver/guardar). Cada uno recibe `property: PropertyDetail | null` y computa su propia porción de UI — la view no expone ningún computed de presentación.
- **Reutilización de un componente compartido en dos contextos de layout distintos sin romper el consumidor existente**: `PropertyPhotoGrid.vue` (usado en `PropertyDetailView.vue` con alto fijo `grid-rows-[200px_200px]`) necesitaba estirarse para igualar la altura de columnas en `EditPropertyView.vue`. Se agregó un prop opcional `expand?: boolean` (default `false`) que cambia a `flex-1 grid-rows-2` solo cuando se pasa explícito — el consumidor original no lo pasa, cero cambio de comportamiento ahí.

## Open questions

- Ninguna.

## Next steps

- Aplicar el mismo criterio (¿esto es orquestación o es lógica/presentación de un dominio específico?) la próxima vez que una view crezca — no esperar a que llegue a 400+ líneas para refactorizar.
