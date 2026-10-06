---
title: "ADR-0008 — TanStack Table (headless) para la tabla admin"
status: stable
last-verified: 2026-07-29
owners: [frontend]
related:
  - "[[adr-no-component-library]]"
  - "[[frontend-admin-panel]]"
  - "[[frontend-architecture]]"
  - "[[adr-admin-offset-pagination]]"
  - "[[adr-vue-cli-deferred-vite-migration]]"
sources: [../../../sources/frontend/2026-07-29-admin-table-tanstack-and-cleanup.md]
decision-date: 2026-07-29
decision-status: accepted
supersedes: la parte operativa de [[adr-no-component-library]] (ADR-0007) — "construir la tabla a mano, TanStack como salida futura"
---

# ADR-0008 — TanStack Table (headless) para la tabla admin

## Contexto

ADR-0007 (un día antes) descartó adoptar una librería de componentes y dejó `@tanstack/vue-table` anotada como salida *si más adelante* hacía falta multi-sort, selección o virtualización. Al ir a construir la tabla surgió la objeción obvia: **si la librería se puede usar hoy, ¿para qué construir algo que después hay que migrar?**

## Decisión

**Adoptar `@tanstack/vue-table` desde el arranque** para la tabla del panel admin.

Compatible con el stack actual, verificado antes de instalar: versión 8.21.3, peer `vue >=3.2` (el proyecto está en 3.5.35) y **agnóstica del bundler** — a diferencia de Nuxt UI, no exige Vite ni Tailwind v4. Por eso esta decisión **no contradice el núcleo de ADR-0007**: lo que ahí se rechazó fue adoptar una librería que arrastrara una migración de build como prerequisito.

## Alternativas consideradas

- **Construirla a mano ahora** (lo que decía ADR-0007). El argumento a favor era esperar al segundo caso de uso para abstraer con evidencia. Perdió frente a la observación de que una API documentada le ahorra a quien llegue después aprender una propia.
- **Esperar al segundo caso de uso.** Descartado por lo mismo.

## Lo que TanStack aporta hoy, y lo que no

Esto se documenta porque define expectativas, no para reabrir la decisión.

- **Es headless**: no trae markup ni estilos. `BaseTable.vue` existe igual y sigue escribiendo `<table>`, `<thead>` y `<td>` a mano. La librería aporta el modelo (columnas, filas, celdas), no la UI.
- **El ordenamiento no se puede usar todavía.** `GetPropertiesAdminRequest` no acepta parámetro de orden ([[adr-admin-offset-pagination]]), y el sorting de TanStack es client-side: reordenaría solo las 20 filas cargadas, con resultado que parece global sin serlo. Por eso **solo se registra `getCoreRowModel`** — sumar `getSortedRowModel` o `getPaginationRowModel` introduciría exactamente ese bug.
- **Paginación y filtros ya son server-side**, así que la librería no participa de ellos.
- **La ceremonia de su API es por features que aún no se usan**: `getHeaderGroups()` devuelve *grupos* porque soporta encabezados anidados (con columnas planas siempre hay uno solo), y `getVisibleCells()` dice "visible" porque permite ocultar columnas en runtime.

Empieza a rendir de verdad cuando el endpoint acepte `sort_by`/`order`, o cuando aparezcan selección de filas o virtualización.

## Consecuencias

- ✅ La forma de definir columnas es una API documentada y no una convención propia.
- ✅ Cuando el backend soporte orden, activarlo es registrar un row model en vez de escribir la lógica.
- ✅ No arrastra prerequisitos de infraestructura: entra en Vue CLI sin tocar el build.
- ❌ Una dependencia más cuyo valor hoy es mayormente potencial: el 100% de lo que se usa (recorrer headers y rows) se escribe a mano en unas 30 líneas.
- ❌ El template es más ceremonioso de leer que un `v-for` sobre columnas propias, por features que no están en uso.
- ⚠️ Sigue vigente lo de ADR-0007: esto **no** abre la puerta a una librería de componentes con estilos propios. TanStack entró justamente por no traer ninguno.

## Claims

- `@tanstack/vue-table` está en `dependencies` en `^8.21.3` ([package.json](frontend/package.json)).
- `BaseTable.vue` registra únicamente `getCoreRowModel` al llamar `useVueTable` ([BaseTable.vue](frontend/src/components/shared/BaseTable.vue)).
- `BaseTable.vue` escribe su propio `<table>`/`<thead>`/`<tbody>`; TanStack no aporta markup ([BaseTable.vue](frontend/src/components/shared/BaseTable.vue)).
- `GetPropertiesAdminRequest` no declara ningún campo de ordenamiento — solo `status`, `verification_status`, `owner_id`, `page` y `page_size` ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
