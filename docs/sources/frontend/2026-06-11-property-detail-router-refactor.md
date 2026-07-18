---
title: PropertyDetailView + router modularization + type refactor
captured-from: conversation
captured-on: 2026-06-11
participants: [raul, claude]
---

## Context
Trabajo de frontend para la vista de detalle de propiedad y limpieza de arquitectura del router y tipos.

## Key conclusions

### Vista de detalle — `PropertyDetailView.vue`
- Ruta: `/listing/:id` — abre en página nueva (no modal).
- Layout en `views/properties/detail/PropertyDetailView.vue`.
- Padding más estrecho que navbar/footer: `px-[8%] sm:px-[12%] lg:px-[18%]`.
- Secciones en orden: photo grid → header (título + badges) → precio → stats chips → descripción → detalles → [POIs mock | mapa Leaflet].
- **Photo grid**: `grid grid-cols-4 grid-rows-[200px_200px]`, 5 celdas con `grid-area` en `<style scoped>` (Tailwind arbitrary values no funciona con clases dinámicas en `v-for`).
- **Stats chips**: `grid grid-cols-3 sm:grid-cols-6` para ancho igual en todos.
- **Badge de verificación**: tooltip en hover — `hidden group-hover:block absolute top-[calc(100%+6px)] right-0 w-56`.
- **Sección inferior**: `flex gap-6`, mitad izquierda POIs (mock), mitad derecha mapa Leaflet con `l-map + l-marker`.
- Fetch real pendiente — hoy usa mock hardcodeado con datos reales de la DB.

### Composable `usePropertyDetail`
- Extrae toda la lógica computed de la view a `composables/properties/usePropertyDetail.ts`.
- Recibe `Ref<PropertyDetail | null>`.
- Exports: `title`, `formattedPrice`, `formattedAdminFee`, `stats`, `details`, `statusLabel`, `statusStyle`, `verificationLabel`, `verificationStyle`, `mapCenter`, `gridImages`.
- Formateo de precios: `Intl.NumberFormat("es-CO", { style: "currency", currency: ..., maximumFractionDigits: 0 })`.

### Tipos — separación UI vs API
- `PropertyCardUI` — shape para UI del feed card; creada en `types/feed.ts`.
- `PropertyCard` — shape del response de la API (ya existía en `types/feed.ts`).
- Razón: `PropertyCard.vue` exportaba una interface `Property` directamente desde el `.vue` — causa error TS2614 al importar desde archivos `.ts`. Fix: mover a `types/feed.ts` como `PropertyCardUI`.
- Tres consumers actualizados: `PropertyCard.vue`, `usePropertyMapper.ts`, `MyPropertiesView.vue`.
- `PropertyDetail` y `PropertyLocationDetail` — en `types/properties.ts`. `PropertyLocationDetail` tiene `city_id` (properties-service sigue usando ese nombre — distinto del rename en catalog-service).
- `PropertyImageCard` importada desde `types/feed.ts` en el type de `PropertyDetail`.

### Router modularizado
- `router/index.ts` — solo instancia el router e importa 5 módulos de rutas. Guard `beforeEach` permanece aquí.
- 5 archivos de rutas en `router/routes/`:
  - `public.ts` — `/`, `/about`
  - `auth.ts` — `/login`, `/register`, `/forgot-password`
  - `settings.ts` — `/settings` + children
  - `properties.ts` — `/properties`, `/listing/:id`, `/feed` + children (`/feed/list`, `/feed/map`)
  - `analytics.ts` — `/avm` (separado de `public` porque es analytics, no landing)
- Motivo: `router/index.ts` tenía >120 líneas y seguía creciendo con cada nueva vista.

### Estructura de vistas reorganizada
- Vistas de propiedades en subfolders por dominio:
  - `views/properties/feed/` — FeedView, MapView
  - `views/properties/dashboard/` — MyPropertiesView
  - `views/properties/detail/` — PropertyDetailView
- Vistas eliminadas de la raíz `views/properties/` (FeedView, MapView, MyPropertiesView, PropertiesView) — todas movidas a subfolders.
- Imports usan alias `@/` — nunca rutas relativas `../`.

## Open questions
- Carousel modal para galería de fotos (vue3-carousel ya instalado) — diferido.
- Fetch real de propiedad por ID — pendiente conectar API layer.
- Mostrar nombre del barrio desde `neighborhood_id` — trivial, pendiente.
- Mostrar info del anunciante (`owner_id`) — requiere llamada separada a users-service + `v-if` para degradar si falla.

## Next steps
- Cablear fetch real en `PropertyDetailView` (`GET /v1/properties/:id`).
- Resolver nombre de barrio desde catalog `by-coordinates` o lookup directo.
- POIs reales desde `ReachablePoiUseCase` cuando esté implementado.
