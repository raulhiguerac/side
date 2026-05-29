---
title: Componente de mapa reusable (MapUser)
status: draft
last-verified: 2026-05-28
owners: [frontend]
related: [[frontend]], [[frontend-architecture]], [[adr-mapbox-geocoding-leaflet-rendering]], [[adr-gmaps-places-geocoding]]
sources: [../../sources/frontend/2026-05-28-avm-form-split-and-dumb-map.md]
---

## TL;DR

`MapUser.vue` (`components/map/`) es el componente de mapa **dumb/controlado** y reusable del frontend: props que entran, eventos que salen, cero estado de negocio. Usa `@vue-leaflet/vue-leaflet` (declarativo). Patrón **híbrido**: una prop `markers` tipada para el caso común + un `<slot>` como escape hatch para cualquier otra capa Leaflet. Los iconos son **data-driven** (SVGs en `public/icons/` elegidos por `marker.imageType`). D3 se suma como **capa plug-and-play** aparte, no dentro del componente.

## Por qué dumb/controlado

El componente se reusa en varios lados (form AVM, futuro feed-mapa, etc.), así que no puede hardcodear *qué* renderiza ni la lógica de negocio. Patrón:
- **Props in**: `center`, `markers`, `zoom` (vía `v-model`).
- **Eventos out**: lo que el mapa emita (clicks, cambios de zoom) los decide el padre.
- El **padre posee los datos y las decisiones**; el componente posee la **instancia Leaflet** (el ciclo de vida del mapa).

## Stack: vue-leaflet declarativo

Se usa `@vue-leaflet/vue-leaflet` (`<l-map>`, `<l-tile-layer>`, `<l-marker>`, `<l-icon>`) en vez de Leaflet crudo imperativo. Ventaja: la reactividad y el ciclo de vida los maneja el wrapper; menos código y menos gotchas (proyección, `invalidateSize`, reconciliación manual de markers). El CSS de Leaflet ya se carga vía `<link>` en `public/index.html` — no hace falta importarlo.

## Patrón híbrido: markers-prop + slot

```
<l-map> + <l-tile-layer>
  ├── <l-marker v-for="markers">  ← caso común, typed (MarkerData[])
  └── <slot/>                      ← escape hatch para capas extra
```

- **`markers: MarkerData[]`** (prop typed) cubre el 90% — el padre solo pasa datos.
- **`<slot>`** permite que el padre componga cualquier otra capa (`<l-circle>`, `<l-geo-json>`, controles...). Los hijos del slot se compilan en el **scope del padre** → `MapUser` **no importa** todos los `L*`, solo `LMap`/`LTileLayer`/`LMarker`/`LIcon`. Cada vista trae lo que usa; el bundle queda flaco.

> Alternativa descartada: importar/registrar los ~22 componentes `L*` en `MapUser` — infla el bundle y sigue hardcodeando qué se renderiza. El slot es el camino "acepta cualquier cosa".

## Zoom controlado (`v-model:zoom` + `defineModel`)

El zoom es two-way y lo posee el padre. `MapUser` usa `const zoom = defineModel<number>("zoom", { default: 15 })` y `<l-map v-model:zoom="zoom">`; el padre escribe `<MapUser v-model:zoom="...">`. `defineModel` crea la prop + el emit `update:zoom` por debajo, así el scroll del usuario sincroniza de vuelta al padre sin mutar una prop.

- `defineModel` requiere **Vue 3.4+** — depende del upgrade a 3.5 (ver [[frontend-architecture]] "Build & tooling"). En 3.2 no corre.
- `center` hoy es **one-way** (`:center`), suficiente para fijar el mapa donde el padre indica. Si se quisiera two-way (panear → vuelve el center), sería otro `defineModel`.
- Escala de zoom Leaflet: 0 = mundo, ~10 ciudad, ~13-15 barrio/calle, ~16-18 manzana, 19 = máximo de tiles OSM. Para un inmueble en Bogotá, ~14-16. Tope opcional con `:max-zoom` (≤ 19 con OSM).

## Iconos data-driven

El tipo de cada marker decide su ícono. Definido en `types/maps.ts`:

```ts
export type MarkerImageType = "subject" | "house" | "apartment" | "food" | "education"; // evoluciona

export interface MarkerData {
  id: string;
  lat: number;
  lon: number;
  imageType: MarkerImageType;
}
```

- **`subject`** = el inmueble que se está avaluando (marker propio, diferenciado de los comparables `house`/`apartment` y de los POIs `food`/`education`...).
- En el `<l-icon>` el `:src` se arma con template literal: `` `/icons/${marker.imageType}.svg` ``.
- **Los SVG viven en `public/icons/`** con `filename === valor del union` (`subject.svg`, `house.svg`, ...). Un `:src` dinámico **solo resuelve para assets en `public/`** — en `src/assets/` el bundler no resuelve strings dinámicos (habría que usar `new URL(..., import.meta.url)` en Vite o `require()` en Vue CLI).
- `MarkerData`/`MarkerImageType` son **una sola fuente de verdad** importada tanto por `MapUser` como por el padre que arma los markers.

## D3 como capa plug-and-play

D3 sobre el mapa (heatmaps, densidad, choropleth) **no va en la view ni dentro de `MapUser`**. Va en un componente/composable dedicado que **consume la instancia Leaflet** que `MapUser` expone (vía `@ready`/`defineExpose`):
- La mecánica D3↔Leaflet (proyectar con `latLngToLayerPoint`, redibujar en `zoomend`/`moveend`, pane SVG) necesita la instancia → vive pegada a ella, no en la view.
- La **data** a visualizar baja desde la view por props (mismo principio data-driven que los markers).
- `MapUser` no importa D3 → solo entra al bundle donde se use la capa. Markers y overlay D3 son panes distintos, conviven sin pisarse.

Ver [[adr-mapbox-geocoding-leaflet-rendering]] para la decisión de stack (Leaflet+D3).

## Estado (2026-05-28)

- Escrito con `defineModel` → **corre recién post-upgrade a Vue 3.5** (planeado 2026-05-29).
- Faltan los SVG en `public/icons/` y cablear el padre (`DevPlaygroundView` → marker `subject` desde el autocomplete).

## Claims

- `MapUser.vue` usa `@vue-leaflet/vue-leaflet` (`LMap`, `LTileLayer`, `LMarker`, `LIcon`) ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- El zoom es two-way vía `defineModel<number>("zoom", { default: 15 })` + `v-model:zoom` en `<l-map>` — requiere Vue 3.4+ ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- `MapUser` expone una prop `markers: MarkerData[]` (v-for de `<l-marker>`) **y** un `<slot>` para capas extra ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- El ícono de cada marker se arma con `` `/icons/${marker.imageType}.svg` `` dentro de un `<l-icon>` ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- `MarkerData` y `MarkerImageType` viven en `types/maps.ts`, exportados; `MarkerImageType` incluye `subject` (el inmueble avaluado) + comparables + POIs ([types/maps.ts](frontend/src/types/maps.ts)).
- El CSS de Leaflet se carga vía `<link>` en `public/index.html`, no por import ([public/index.html:11](frontend/public/index.html#L11)).
