---
title: Filtros del panel admin en la URL y tab de importaciones cableada
captured-from: conversation
captured-on: 2026-08-24
participants: [author, claude]
---

## Context

La tab de moderación listaba 18.744 filas sin forma de acotarlas y la de importaciones era un empty state fijo, porque el backend no listaba jobs. Se decidió montar `AdminFilterBar` —que existía sin usar— y cablear el historial de imports, con los filtros viviendo en la query y no en un `ref` del composable.

## Key conclusions

- **La URL es la fuente de verdad de los filtros admin.** El ciclo es: `@apply` → `router.push({ query })` → un `watch` sobre la query saneada llama a `load`. El componente nunca se cree a sí mismo: cambiar un select solo raya su borrador, y solo el click emite. Sin bucle porque rellenar el borrador no es un click.
- **Un solo camino de carga.** El `watch` con `immediate: true` cubre el montaje, así que no hay `onMounted(load)` aparte: dos caminos se desincronizan.
- **`push` y no `replace`**, para que el back del navegador deshaga el filtro.
- **La query se sanea contra las `options` de cada filtro**, que son el enum del backend. Valores desconocidos y keys repetidas (llegan como array) se descartan en silencio; `?status=banana` no llega a pedir un 422. Vive en `utils/adminFilters.ts`.
- **Aplicar sin filtros emite `{}`**, no `status=""`: la ausencia de param es "sin filtrar", y el string vacío sería un 422 contra el enum.
- **`AdminSplitView` gana un slot `filters`** en la columna izquierda, sobre la tabla, con `v-if="$slots.filters"` para no dejar margen fantasma en las vistas que no lo usan.
- **La página sigue en memoria, a propósito.** `usePagination` acumula páginas e incrementa; soportar `?page=3` obligaría a cargar 1-3 o migrar a offset puro. Bookmarkear filtros cubre el caso real.
- **`AdminFilterBar` solo hace `<select>`.** `has_errors` entra como dos opciones `"true"`/`"false"` (Pydantic las parsea a bool); los filtros de fecha quedan fuera hasta que el componente soporte inputs de fecha.
- **La tab de importaciones se diseñó primero como mock estático** —datos ficticios, banner ámbar, botones inertes— para revisar el layout antes de que existiera el endpoint, y después se cableó.
- **El panel de un job recibe la fila entera, no solo el id.** El endpoint de status no devuelve `expires_at` ni `retry_of_job_id`, que son los que deciden si se puede relanzar; la fila ya está en memoria. El fetch de errores no se dispara si `error_count` es 0.
- **`useBulkJobs` se calcó de `useActivePromotions`** (pide siempre la página al servidor) y no de `useAdminProperties` (acumula en memoria): relanzar agrega una corrida arriba y una copia local se desalinea.
- **Auditoría de endpoints admin: 11 de 12 cableados.** El único huérfano es `POST /properties/{id}/estimated-price`, que además no invalida cache y cuyos campos no están expuestos en ningún schema público.

## Open questions

- El botón de relanzar y el de descargar CSV de errores están puestos pero inertes: falta el endpoint de retry.
- Un job `failed` global muestra `0/0` y no explica por qué falló: la tabla guarda errores por fila, no un mensaje de error de job.
- Una cadena de tres o cuatro reintentos del mismo archivo es difícil de seguir en una lista plana.
- La selección del panel (`selectedId`) sigue en un `ref` y no en la URL, en las cuatro vistas.

## Next steps

- Refactorizar las cuatro vistas admin a un `useAdminList<T>` más un contenedor con slots, y extraer el trío de filtros de URL a un `useUrlFilters(definitions)` — la salida no es un factory de componentes. Anotado en open items, para cuando el retry esté cerrado y las vistas dejen de moverse.
