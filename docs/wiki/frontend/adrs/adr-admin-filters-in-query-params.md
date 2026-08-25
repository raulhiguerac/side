---
title: "ADR-0012 — Los filtros del panel admin viven en la URL, no en el composable"
status: stable
last-verified: 2026-08-24
owners: [frontend]
related:
  - "[[frontend-admin-panel]]"
  - "[[adr-admin-tabs-nested-routes]]"
  - "[[adr-admin-offset-pagination]]"
  - "[[properties-service-admin]]"
  - "[[open-items]]"
sources: [../../../sources/frontend/2026-08-24-admin-url-filters-and-imports-tab.md]
decision-date: 2026-08-24
decision-status: accepted
---

# ADR-0012 — Los filtros del panel admin viven en la URL, no en el composable

## Contexto

`useAdminProperties` guardaba los filtros en un `ref` propio y la vista cargaba con `onMounted(load)` sin pasarle nada. El backend acepta `status`, `verification_status`, `owner_id` e `is_promoted` desde hace tiempo; lo que faltaba era la UI y, sobre todo, decidir **dónde vive** ese estado.

[[adr-admin-tabs-nested-routes]] ya había elegido rutas anidadas apostando a que los filtros terminaran en query params, pero esa mitad quedó pendiente hasta acá. La pregunta concreta: ¿el botón "Aplicar" llama a `load(filtros)` directo, o empuja a la URL y algo reacciona?

## Decisión

**Los filtros son query params, y la URL es la única fuente de verdad.** El ciclo es `@apply` → `router.push({ query })` → un `watch` sobre la query saneada llama a `load`.

Tres consecuencias de forma que no son negociables si se quiere que funcione:

- **Un solo camino de carga.** El `watch` va con `{ immediate: true }` y reemplaza al `onMounted(load)`; dos caminos de carga se desincronizan en cuanto uno crezca.
- **La query se sanea contra las `options` de cada filtro**, que son el mismo enum que valida el backend. Un valor desconocido o una key repetida (llega como array) se descartan en silencio, así que `?status=banana` nunca se convierte en un 422.
- **`push` y no `replace`**, para que el botón atrás del navegador deshaga el filtro anterior.

El componente de filtros no decide nada: mantiene un borrador local que solo sale al hacer click, y se resiembra desde la URL cuando esta cambia. No hay bucle porque rellenar el borrador no emite.

## Alternativas consideradas

- **Filtros en el `ref` del composable** (lo que había). Más corto, pero se pierden en el reload, no se comparten por link y el botón atrás no los deshace. Es exactamente el estado que [[adr-admin-tabs-nested-routes]] quería en la URL.
- **Un store de Pinia para el estado del panel.** Sobrevive el cambio de tab, pero no el reload ni el link compartido, y agrega una capa para representar algo que la URL guarda gratis.
- **Emitir los valores ya tipados desde el componente de filtros.** Descartado: obligaría al componente a conocer los enums del backend. Emite strings y el saneo vive en un helper (`utils/adminFilters.ts`), que es lo que también protege contra la URL escrita a mano.

## Consecuencias

- ✅ La cola filtrada es bookmarkeable y compartible: "las corridas fallidas de esta semana" es un link.
- ✅ Reload y botón atrás funcionan sin código extra, y el mismo patrón sirve para las cuatro tabs.
- ✅ La URL escrita a mano no puede provocar un 422: el saneo corre antes del request.
- ❌ Aplicar el mismo filtro que ya está activo no refetchea: `push` a la misma URL es una navegación duplicada y el `watch` no se entera. Se aceptó — pedir lo que ya se está viendo no es un caso que valga código.
- ⚠️ La página **no** viaja en la URL: `usePagination` acumula páginas en memoria y entrar directo en `?page=3` obligaría a cargar 1-3 o migrar a offset puro. Bookmarkear filtros cubre el caso real; la selección del panel (`selectedId`) sigue igualmente fuera de la URL.
- ⚠️ `AdminFilterBar` solo renderiza `<select>`. Filtros que no sean de opciones cerradas —fechas, texto libre— necesitan extender el componente antes de poder exponerse.

## Claims

- `AdminFilterBar` emite `apply` con los valores elegidos y omite los vacíos, y solo el click emite ([AdminFilterBar.vue](frontend/src/components/admin/shared/AdminFilterBar.vue)).
- `sanitizeFilterQuery` descarta las keys no declaradas y los valores que no estén en `options`, y ignora las que llegan como array ([adminFilters.ts](frontend/src/utils/adminFilters.ts)).
- `AdminModerationView` y `AdminImportsView` cargan desde un `watch` sobre la query con `immediate: true`, y ninguna llama a `load` en `onMounted` ([AdminModerationView.vue](frontend/src/views/admin/properties/moderation/AdminModerationView.vue), [AdminImportsView.vue](frontend/src/views/admin/properties/imports/AdminImportsView.vue)).
- Las dos vistas aplican filtros con `router.push({ query })` ([AdminModerationView.vue](frontend/src/views/admin/properties/moderation/AdminModerationView.vue), [AdminImportsView.vue](frontend/src/views/admin/properties/imports/AdminImportsView.vue)).
- `AdminSplitView` declara un slot `filters` que se renderiza sobre la tabla en la columna izquierda ([AdminSplitView.vue](frontend/src/components/admin/shared/AdminSplitView.vue)).
