---
title: Componente de mapa reusable (MapUser)
status: stable
last-verified: 2026-06-09
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[adr-mapbox-geocoding-leaflet-rendering]]"
  - "[[adr-gmaps-places-geocoding]]"
sources: [../../sources/frontend/2026-05-28-avm-form-split-and-dumb-map.md, ../../sources/frontend/2026-05-29-vue35-gmaps-places-leaflet-markers.md, ../../sources/frontend/2026-05-29-avm-form-wiring-predict.md, ../../sources/frontend/2026-06-09-mapview-leaflet-implementation.md]
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

## Zoom y center controlados (`v-model` + `defineModel`)

Tanto `zoom` como `center` son two-way y los posee el padre. `MapUser` usa `defineModel` para ambos:

```ts
const zoom = defineModel<number>("zoom", { default: 15 });
const center = defineModel<[number, number]>("center");
```

Y los pasa a `<l-map>` como `v-model:zoom="zoom"` y `v-model:center="center"`. El padre escribe `<MapUser v-model:zoom="zoom" v-model:center="center">`.

- `defineModel` requiere **Vue 3.4+** — upgrade a 3.5 ya completado (ver [[frontend-architecture]]).
- Escala de zoom Leaflet: 0 = mundo, ~10 ciudad, ~13-15 barrio/calle, ~16-18 manzana, 19 = máximo tiles OSM. Feed-mapa usa `:min-zoom="14"` `:max-zoom="17"`.

### Race condition crítica: inicialización del center

vue-leaflet registra su watcher de `center` **dentro de un `onMounted` async** (necesita await del import dinámico de Leaflet). Si el padre actualiza `center.value` también en `onMounted`, el watcher puede no estar registrado aún → el mapa ignora el pan.

**Fix**: inicializar `center` **síncronamente** desde `localStorage` en el script setup del padre, antes de que el mapa monte:

```ts
function getInitialCenter(): [number, number] {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.USER_LOCATION);
    if (raw) {
      const loc = JSON.parse(raw);
      if (loc.latitude && loc.longitude) return [loc.latitude, loc.longitude];
    }
  } catch {}
  return [4.681414, -74.046864]; // Bogotá fallback
}
const center = ref<[number, number]>(getInitialCenter());
```

Así el mapa arranca ya en la ubicación correcta sin necesitar un `setView` posterior. No intentar actualizar `center.value` desde `onMounted` — la race condition es no-obvia y difícil de reproducir en dev (depende de timing del import dinámico de Leaflet).

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
- Los iconos son **componentes Lucide** (no SVGs en `public/icons/`). El mapeo `MarkerImageType → Component` vive en `constants/markerIcons.ts` como `Record<MarkerImageType, Component>` — p.ej. `house: MapPinHouse`, `apartment: Building`, `food: ChefHat`, `education: NotebookPen`.
- En el template: `<component :is="markerIconMap[marker.imageType]" :size="24" color="#22C55E" />` dentro del `<l-icon>`.
- `MarkerData`/`MarkerImageType` son **una sola fuente de verdad** importada tanto por `MapUser` como por el padre que arma los markers.

### Gotchas de `l-icon` con componentes Vue

`<l-icon>` genera un `div` con estilos Leaflet visibles (borde, sombra, fondo). Para iconos Lucide (no pins tradicionales):

- Limpiar el contenedor: `class-name="!bg-transparent !border-0 !shadow-none"` en `<l-icon>`.
- **Anchor**: depende de la forma del icono. Para iconos cuadrados: `[w/2, h/2]` (centro). Para pins con punta abajo (como en MapView feed-mapa): `[w/2, h]` — e.g. `[12, 24]` para icono 24×24. Usar `[16, 32]` o valores fuera de bounds hace que el marcador se desplace.
- El componente Lucide necesita `color` explícito — dentro del div de Leaflet `currentColor` no resuelve a ningún color visible.
- **Lucide `Building` es stroke-only** — pasar `:fill` no tiene efecto. Para cambiar el fondo, envolver en un `div` con clase de background: `<div class="rounded-full bg-[#1e3a5f]"><Building :size="14" color="#FFF" /></div>`.

### Hover state en feed-mapa (MapView)

`MapView` pasa `hoveredId: string | null` como prop a `MapUser`. El marcador activo usa icono más grande y color verde:

- Normal: tamaño 24×24, anchor `[12, 24]`, fondo `#1e3a5f`
- Hover: tamaño 48×48, anchor `[24, 48]`, fondo `#22C55E`

`hoveredId` se setea en `@mouseenter`/`@mouseleave` de cada `PropertyCard` en la vista padre.

## D3 como capa plug-and-play

D3 sobre el mapa (heatmaps, densidad, choropleth) **no va en la view ni dentro de `MapUser`**. Va en un componente/composable dedicado que **consume la instancia Leaflet** que `MapUser` expone (vía `@ready`/`defineExpose`):
- La mecánica D3↔Leaflet (proyectar con `latLngToLayerPoint`, redibujar en `zoomend`/`moveend`, pane SVG) necesita la instancia → vive pegada a ella, no en la view.
- La **data** a visualizar baja desde la view por props (mismo principio data-driven que los markers).
- `MapUser` no importa D3 → solo entra al bundle donde se use la capa. Markers y overlay D3 son panes distintos, conviven sin pisarse.

Ver [[adr-mapbox-geocoding-leaflet-rendering]] para la decisión de stack (Leaflet+D3).

## Estado (2026-06-09)

- Vue 3.5 upgrade completado — `defineModel` y `useTemplateRef` funcionan.
- Iconos migrados a Lucide (`markerIconMap` en `constants/markerIcons.ts`).
- `center` migrado a `defineModel` two-way (antes era one-way `:center`).
- `MapUser` usado en `DevPlaygroundView` (AVM) y `MapView` (feed-mapa).
- Race condition de center documentada y resuelta con inicialización síncrona desde localStorage.

## Claims

- `MapUser.vue` usa `@vue-leaflet/vue-leaflet` (`LMap`, `LTileLayer`, `LMarker`, `LIcon`) ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- El padre debe pasar `:markers="marker ? [marker] : []"` cuando el marker puede ser `null` ([views/dev/DevPlaygroundView.vue](frontend/src/views/dev/DevPlaygroundView.vue)).
- `zoom` y `center` son two-way vía `defineModel` + `v-model:` en `<l-map>` — requiere Vue 3.4+ ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- vue-leaflet registra su watcher de `center` dentro de un `onMounted` async — actualizar `center.value` desde el padre en `onMounted` crea una race condition; el fix es inicializar el ref síncronamente en script setup ([views/properties/MapView.vue](frontend/src/views/properties/MapView.vue)).
- `MapUser` expone una prop `markers: MarkerData[]` (v-for de `<l-marker>`) **y** un `<slot>` para capas extra ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- Los iconos de marker son componentes Lucide resueltos por `markerIconMap` (`Record<MarkerImageType, Component>`) — renderizados con `<component :is="markerIconMap[marker.imageType]">` ([constants/markerIcons.ts](frontend/src/constants/markerIcons.ts)).
- `<l-icon>` requiere `class-name="!bg-transparent !border-0 !shadow-none"` para limpiar el contenedor Leaflet ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- Anchor para pins con punta: `[w/2, h]` (e.g. `[12, 24]`). Anchor para iconos cuadrados: `[w/2, h/2]` (e.g. `[12, 12]`) ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- Lucide `Building` es stroke-only — `:fill` no tiene efecto; usar div wrapper con bg color para cambiar el fondo ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- `MarkerData` y `MarkerImageType` viven en `types/maps.ts` ([types/maps.ts](frontend/src/types/maps.ts)).
- El CSS de Leaflet se carga vía `<link>` en `public/index.html`, no por import ([public/index.html:11](frontend/public/index.html#L11)).
