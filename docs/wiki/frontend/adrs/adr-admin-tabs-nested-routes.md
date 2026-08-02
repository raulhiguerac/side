---
title: "ADR-0009 — Las tabs del panel admin son rutas hijas, no un switch de componentes"
status: stable
last-verified: 2026-08-01
owners: [frontend]
related:
  - "[[frontend-admin-panel]]"
  - "[[frontend-architecture]]"
  - "[[adr-hash-history-static-hosting]]"
  - "[[adr-admin-offset-pagination]]"
  - "[[properties-service-admin]]"
sources: [../../../sources/frontend/2026-08-01-admin-panel-tabs-moderation-preview.md]
decision-date: 2026-08-01
decision-status: accepted
---

# ADR-0009 — Las tabs del panel admin son rutas hijas, no un switch de componentes

## Contexto

`/admin/properties` era una sola vista con la tabla, el botón de importar CSV y todo lo demás, encaminada a un scroll largo donde el admin tendría que buscar qué necesita. El dominio admin de properties tiene 12 endpoints que se agrupan naturalmente en tres áreas —moderación, promociones, importaciones— así que la vista pedía partirse.

La pregunta concreta: ¿las tabs cambian de componente dentro de la misma vista, o son rutas hijas con su propio `<RouterView />`?

Visualmente el resultado es idéntico. La decisión es de mecanismo.

## Decisión

**Rutas hijas.** `/admin/properties` pasa a ser un layout padre (header + barra de tabs + `<RouterView />`) con tres hijos: `""` (moderación, el default), `promotions` e `imports`.

El argumento que decide es el **estado de los filtros**. La tabla de moderación filtra por `status`, `verification_status`, `owner_id` y página; el backend ya acepta esos parámetros y `useAdminProperties` ya los transporta. Con rutas, ese estado vive en query params: sobrevive el cambio de tab, sobrevive el reload, es compartible por link y el botón atrás del navegador funciona. Con un switch de componentes habría que inventar un store solo para que no se pierda, y el reload seguiría volviendo a cero.

Lo demás refuerza sin decidir: cada tab es un chunk lazy aparte, cada vista hace su propio fetch al entrar en vez de montar las tres de una, y el `meta` del guard vive donde ya viven las demás rutas.

## Alternativas consideradas

- **Tabs como switch de componentes** (`v-if`/`v-show` sobre un `selected` local). Más corto de escribir y sin archivos de ruta nuevos. Perdió por lo de los filtros: el estado que hay que preservar es exactamente el que la URL guarda gratis.
- **Una vista por tab sin layout compartido**, repitiendo header y tabs en cada una. Descartado por duplicación obvia.

## Detalles de implementación que no son arbitrarios

- **El padre no lleva `name`.** Tiene un hijo con `path: ""`; nombrar a los dos hace ambiguo un `push({ name: "admin-properties" })` y Vue Router lo advierte. El nombre va en el hijo, que es el destino real.
- **`meta` solo en el padre.** El guard resuelve con `to.matched.some(...)` y `matched` incluye los registros padre, así que repetirlo en cada hijo es ruido.
- **`RouterLink` con `custom` + `v-slot`, leyendo `isExactActive`.** Con las props `active-class`/`exact-active-class` las dos variantes de clase conviven en el atributo (`border-transparent` y `border-brand-primary`, misma familia de utilidades) y cuál gana lo decide el orden en que Tailwind emitió el CSS, no el orden del atributo — o sea, resultado no determinista. El `v-slot` permite un ternario explícito. Renderizar un `<a>` real conserva además el click del medio y "abrir en pestaña nueva".
- **`isExactActive` y no `isActive`**, porque `/admin/properties` es prefijo de las otras dos rutas: con activo por prefijo, la tab de moderación quedaría encendida estando parado en cualquier otra.
- **El detalle de una propiedad no es una tab ni una ruta hija.** Se resolvió como panel lateral dentro de moderación (ver [[frontend-admin-panel]]), porque moderar es recorrer filas y una ruta aparte haría perder filtros y página en cada ida y vuelta. La selección debería terminar en un query param por el mismo motivo que los filtros — todavía no está hecho.

## Consecuencias

- ✅ Filtros, página y (a futuro) selección viven en la URL: reload, deep link y botón atrás funcionan sin código extra.
- ✅ Cada tab se descarga y monta sola; agregar una es un archivo de ruta más, sin tocar las demás.
- ✅ El header y las tabs no se re-renderizan al cambiar de tab: solo cambia el `<RouterView />`.
- ❌ Más archivos: un layout, tres vistas y un árbol de rutas anidado donde antes había una sola vista.
- ⚠️ Al montarse cada vista de nuevo al entrar, el estado local que no esté en la URL se pierde. Es deseable para datos que conviene refrescar, pero obliga a poner en la URL todo lo que sí debe sobrevivir.

## Claims

- `adminPropertiesRoutes` declara `/admin/properties` con `children` y sin `name` en el registro padre ([router/routes/admin/properties.ts](frontend/src/router/routes/admin/properties.ts)).
- El hijo con `path: ""` lleva `name: "admin-properties"` ([router/routes/admin/properties.ts](frontend/src/router/routes/admin/properties.ts)).
- Solo el registro padre declara `meta: { requiresAuth: true, requiresAdmin: true }` ([router/routes/admin/properties.ts](frontend/src/router/routes/admin/properties.ts)).
- `AdminPropertiesLayout.vue` usa `RouterLink` con la prop `custom` y aplica clases según `isExactActive` del slot ([AdminPropertiesLayout.vue](frontend/src/views/admin/properties/AdminPropertiesLayout.vue)).
- `AdminPropertiesLayout.vue` no importa las vistas hijas: las monta vía `<RouterView />` ([AdminPropertiesLayout.vue](frontend/src/views/admin/properties/AdminPropertiesLayout.vue)).
- Los filtros de `useAdminProperties` viven en un `ref` del composable, todavía no en query params ([useAdminProperties.ts](frontend/src/composables/admin/useAdminProperties.ts)).
