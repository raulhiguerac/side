---
title: Acciones del panel de barrios, layout de filtros admin y auditoría de smells del front
captured-from: conversation
captured-on: 2026-10-05
participants: [author, claude]
---

## Context
Se revisó qué endpoints admin de catalog-service no consume el front, se empezaron las acciones del panel de barrios y se ajustó el layout de los filtros admin. Al pedir que el front quede production grade se hizo una auditoría de smells; se resolvió buena parte y el resto pasó a open-items.

## Key conclusions
- De los 14 endpoints `/v1/admin/*` de catalog, el front consume 3 (lecturas de barrios). Faltan las 11 escrituras. Localidades y países solo tienen `GET` públicos (solo activos), y las divisiones no tienen ningún listado.
- `NeighborhoodMap` se queda solo de lectura: `POST /admin/neighborhoods/{id}/geometry` recibe un archivo GeoJSON, no una geometría dibujada. Editar vértices sobre el mapa sería otro proyecto (leaflet-geoman y un endpoint JSON).
- `AdminActionBar` es tonta: recibe `AdminAction<K>[]` (`key`, `icon`, `label`, `variant` default|primary|danger), es genérica sobre `K` y emite `action(key)`. Es una grid de columnas de 1/3, máximo 3 y centradas. Labels cortos ("Geometría"), porque "Actualizar geometría" no cabía.
- La barra no recibe componentes. Quien la usa resuelve la key: el panel reemite `action` y la vista monta un único `BaseModal`. El mapa de modales va por `key` (estable), no por `label`, que cambia entre Activar y Desactivar. Los modales comparten el contrato `neighborhood` + `close` / `saved`.
- `AdminFilterBar` es una grid en la que el botón "Aplicar" es una celda más. Columnas = `n+1` hasta 4 en una fila; desde 5 elementos, `ceil((n+1)/2)`. Con 5 filtros queda 3+3; con 2, una fila de 3. Se descartaron "mínimo 3 columnas" (2 filtros quedaban flotando con huecos), el reparto 80/20 (dejaba una "L" vacía) y centrar el botón en vertical. La prop `filtersWidth` desaparece.
- Reglas de código acordadas: comentarios de una línea, preferiblemente inline; tipos como `interface` en `types/`; constantes en `constants/<dominio>`; HTTP en `api/`, nunca dentro de una constante.
- Refactors hechos (14 commits atómicos):
  - definiciones de filtros en `constants/{properties,catalog}Filters.ts`;
  - `useUrlFilters`, `AdminPaginationFooter` + `pageRange`;
  - `PROPERTY_TYPE_LABELS` / `LISTING_TYPE_LABELS` + `propertyTitle()`;
  - `formatNumber` / `formatArea` / `LOCALE`;
  - un único `PrimaryButton` (`size`, `loading`);
  - `utils/logger`, tuteo, cero `any` salvo `BaseTable`;
  - paleta en `src/theme/brandColors.json`, compartida por Tailwind y JS;
  - `HouseCard` borrado.
- Al unificar `PrimaryButton` cambia la UI: desaparecen el gradiente de editar y crear propiedad y el hover que elevaba los botones admin. Deshabilitado pasa a fondo verde claro y el spinner va junto al texto.
- Hallazgos:
  - **vue-tsc nunca se había ejecutado.** `npx vue-tsc` baja un TypeScript incompatible y aborta. Corre con `npx -p vue-tsc@2 -p typescript@5.6 vue-tsc --noEmit`.
  - **Tiparlo destapó un bug.** `useCities` hacía `.map` sobre `undefined`.
  - **`disabled:` funciona.** El variant de Vueform genera `[disabled] .x, .x[disabled]`, que sí aplica sobre el propio elemento.

## Open questions
- `App.vue` conserva el CSS de la plantilla de Vue CLI (`#app { font-family: Avenir… }`), que probablemente pisa Plus Jakarta Sans. No se tocó porque cambia la tipografía global.
- ¿El aviso de superposición y el número de vértices entran en el panel de barrios?

## Next steps
- `AdminFormModal` (cascarón sobre `BaseModal`) y los tres modales reales de barrios: Editar → `PATCH`, Geometría → upload GeoJSON, Desactivar/Activar → `PATCH is_active`. Después, `onSaved` recarga el detalle y la tabla.
- Actualizar en open-items los ítems "esqueleto admin copiado" y "panel de barrios: faltan las acciones", que quedaron parcialmente resueltos.
- Script `typecheck` con `vue-tsc` como devDependency, y arreglar `ResetPasswordView:51` y `AdminModerationForm:52/81`.
