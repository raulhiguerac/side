---
title: "ADR-0007 — Sin librería de componentes: la tabla admin se construye a mano"
status: stable
last-verified: 2026-07-29
owners: [frontend]
superseded-by: "[[adr-tanstack-table]] (parcial — solo la decisión de construir la tabla a mano)"
related:
  - "[[adr-tanstack-table]]"
  - "[[frontend-architecture]]"
  - "[[frontend-admin-panel]]"
  - "[[adr-vue-cli-deferred-vite-migration]]"
  - "[[adr-admin-offset-pagination]]"
sources: [../../../sources/frontend/2026-07-28-admin-panel-groundwork.md]
decision-date: 2026-07-28
decision-status: accepted
---

# ADR-0007 — Sin librería de componentes: la tabla admin se construye a mano

> **Superado parcialmente el 2026-07-29 por [[adr-tanstack-table]].** Al día siguiente de tomarse, se adoptó `@tanstack/vue-table` en vez de construir la tabla a mano.
>
> **Cae** la alternativa de abajo que dejaba TanStack como salida futura: se adoptó de entrada.
>
> **Sigue vigente** todo lo demás, que es el núcleo: Nuxt UI no encaja porque exigiría migrar a Vite y a Tailwind v4, y no se adopta ninguna librería que traiga estilos propios o que dicte el build tool. TanStack entró justamente por no hacer ninguna de las dos cosas.

## Contexto

El panel admin necesita una tabla de moderación: filas densas, columnas ordenables, acciones por fila, filtros en la misma vista ([[frontend-admin-panel]]). Es el primer componente del proyecto que no es trivial de hacer a mano, así que surgió la pregunta razonable de si vale la pena adoptar una librería de componentes — concretamente **Nuxt UI**, que hoy es la opción más visible del ecosistema Vue.

Hasta ahora el proyecto no usa ninguna: todo es custom sobre tokens `brand-*` de Tailwind.

## Decisión

**No adoptar librería de componentes. La tabla admin se construye a mano** con los tokens `brand-*` que ya existen.

El motivo no es preferencia estética: **Nuxt UI no encaja en este stack**. `@nuxt/ui` v3 corre en Vue plano, sí, pero se instala como **plugin de Vite** y requiere **Tailwind v4**. Este proyecto es Vue CLI (webpack) sobre Tailwind v3, así que adoptarlo significa migrar el build **y** subir una major de Tailwind — trabajo de infraestructura, no "agregar una librería de componentes".

Y de las dos migraciones, la de Tailwind es la que **no depende de nosotros**: `tailwind.config.js` carga `@vueform/vueform/tailwind` y Vueform 1.13 apunta a v3 (detalle en [[adr-vue-cli-deferred-vite-migration]]).

## Alternativas consideradas

- **Nuxt UI ahora.** Descartado: arrastra la migración a Vite + Tailwind v4 como prerequisito. Sería dejar que la elección de un componente decida el build pipeline del proyecto entero.
- **Migrar a Vite y Tailwind v4 primero, después Nuxt UI.** Es el orden correcto si algún día se quiere, pero invierte las prioridades: hoy el panel admin tiene 10 endpoints sin cablear y ninguna vista de moderación. Construir la tabla no está bloqueado por nada.
- **PrimeVue / Element Plus** (bundler-agnósticos, sí correrían acá). Descartados por costo de estilo: traen su propio sistema de theming, que habría que reconciliar con los tokens `brand-*` existentes. Se pagaría integración para no escribir un `<table>`.
- **`@tanstack/vue-table`.** No descartado — **diferido**. Es headless (lógica sin markup ni estilos) y agnóstico del bundler, así que entra sin tocar nada del build. Es la salida si la tabla llega a necesitar multi-sort, selección de filas o virtualización. Hoy no las necesita: la paginación es offset con `total` del servidor ([[adr-admin-offset-pagination]]), no scroll infinito. — **Esta es la parte que cayó**: se adoptó al día siguiente sin esperar a esos casos de uso. Ver [[adr-tanstack-table]].

## Consecuencias

- ✅ La tabla admin no bloquea nada ni arrastra prerequisitos de infraestructura.
- ✅ La consistencia visual sale gratis: mismos tokens `brand-*` que el resto de la app, sin reconciliar dos sistemas de theming.
- ✅ La decisión de migrar a Vite queda libre de tomarse por sus propios méritos, no forzada por una librería de UI.
- ❌ Hay que escribir a mano orden por columna, estado vacío, estado de carga y responsive de la tabla. Es más código nuestro y más superficie de bugs.
- ❌ Cada componente admin nuevo (modales, dropdowns, tooltips) repite la decisión. Si la cuenta crece bastante, conviene reevaluar en vez de acumular por inercia.
- ⚠️ Esto **no** es "nunca una librería de componentes". Es "no una que dicte el build tool". Si se ejecuta la migración a Vite y Tailwind v4 por otras razones, Nuxt UI vuelve a la mesa.

## Claims

- El proyecto no declara ninguna librería de componentes en `package.json`; los componentes son custom sobre utilidades de Tailwind ([package.json](frontend/package.json)).
- `tailwind.config.js` define tokens `brand-*` (`brand-primary`, `brand-text`, `brand-bg`, `brand-muted`, `brand-divider`) usados directamente en los templates ([tailwind.config.js](frontend/tailwind.config.js)).
- `tailwind.config.js` carga `require("@vueform/vueform/tailwind")` como plugin, lo que ata la major de Tailwind a la que soporte Vueform ([tailwind.config.js:30](frontend/tailwind.config.js#L30)).
- Los scripts de build son `vue-cli-service`, no Vite ([package.json:5-9](frontend/package.json#L5-L9)).
- `GET /admin/properties` devuelve `AdminPropertiesPage` con `items`/`total`/`page`/`page_size` — paginación por offset, sin scroll infinito ([admin_schemas.py](backend/properties-service/src/app/services/admin/schemas/admin_schemas.py)).
