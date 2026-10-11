---
title: Componente de mapa reusable (MapUser)
status: stable
last-verified: 2026-10-09
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[frontend-poi-reachable]]"
  - "[[adr-mapbox-geocoding-leaflet-rendering]]"
  - "[[adr-gmaps-places-geocoding]]"
  - "[[adr-feed-map-whole-bbox-cluster]]"
sources:
  - ../../sources/frontend/2026-05-28-avm-form-split-and-dumb-map.md
  - ../../sources/frontend/2026-05-29-vue35-gmaps-places-leaflet-markers.md
  - ../../sources/frontend/2026-05-29-avm-form-wiring-predict.md
  - ../../sources/frontend/2026-06-09-mapview-leaflet-implementation.md
  - ../../sources/frontend/2026-06-15-poi-detail-view-mapuser-cluster.md
  - ../../sources/frontend/2026-06-20-property-detail-view-refactor.md
  - ../../sources/frontend/2026-10-04-admin-neighborhoods-tab.md
  - ../../sources/frontend/2026-10-09-api-layer-map-cluster-and-typecheck.md
---

## TL;DR

`MapUser.vue` (`components/map/`) es el componente de mapa **dumb/controlado** y reusable del frontend: props que entran, eventos que salen, cero estado de negocio. Usa `@vue-leaflet/vue-leaflet` para el mapa, los tiles y el marcador `subject`; **todos los demás marcadores** (propiedades y POIs) van a un cluster imperativo, `useMarkerCluster`, desde el 2026-10-09. Patrón **híbrido**: una prop `markers` tipada + un `<slot>` como escape hatch para cualquier otra capa Leaflet. Los iconos son **data-driven**: componentes lucide elegidos por `marker.imageType` vía `markerIconMap`. D3 se suma como **capa plug-and-play** aparte, no dentro del componente.

## Por qué dumb/controlado

El componente se reusa en varios lados (form AVM, futuro feed-mapa, etc.), así que no puede hardcodear *qué* renderiza ni la lógica de negocio. Patrón:
- **Props in**: `center`, `markers`, `zoom` (vía `v-model`).
- **Eventos out**: `bbox` (en cada `moveend`), `markerClick(id)` y `markerHover(id | null)`; qué hacer con ellos lo decide el padre.
- El **padre posee los datos y las decisiones**; el componente posee la **instancia Leaflet** (el ciclo de vida del mapa).

## Stack: vue-leaflet declarativo

Se usa `@vue-leaflet/vue-leaflet` (`<l-map>`, `<l-tile-layer>`, `<l-marker>`, `<l-icon>`) en vez de Leaflet crudo imperativo. Ventaja: la reactividad y el ciclo de vida los maneja el wrapper; menos código y menos gotchas (proyección, `invalidateSize`, reconciliación manual de markers). El CSS de Leaflet ya se carga vía `<link>` en `public/index.html` — no hace falta importarlo.

## Patrón híbrido: markers-prop + slot

```
<l-map> + <l-tile-layer>
  ├── <l-marker v-for="subjectMarkers">  ← solo el inmueble avaluado, con <l-icon>
  ├── useMarkerCluster(markers ≠ subject) ← propiedades y POIs, imperativo
  └── <slot/>                             ← escape hatch para capas extra
```

- **`markers: MarkerData[]`** (prop typed) cubre el 90% — el padre solo pasa datos; `MapUser` decide qué va al cluster.
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

### `internalCenter` — por qué el `defineModel center` NO se pasa directamente a `l-map`

Leaflet emite objetos `LatLng` propios (no tuples `[number, number]`) en el evento `update:center` cuando el usuario hace pan. Si `defineModel center` está vinculado directo a `l-map` con `v-model:center="center"`, ese objeto `LatLng` contamina el ref del padre. En el siguiente ciclo reactivo, Leaflet llama `setLatLng` con su propio `LatLng` recibido de vuelta como prop y falla con `Invalid LatLng object: (undefined, undefined)`.

**Fix:** `internalCenter` es un ref interno que `l-map` posee libremente:

```ts
const center = defineModel<[number, number]>("center");
const internalCenter = ref<[number, number]>(center.value ?? [4.681414, -74.046864]);

watch(center, (val) => {
  if (val) internalCenter.value = val;
});
```

Template: `v-model:center="internalCenter"` en `<l-map>`. El padre pasa el centro inicial y puede moverlo programáticamente (vía `v-model:center`); cuando el usuario hace pan, `internalCenter` se actualiza localmente sin contaminar el estado del padre. El bbox se emite por `@moveend` — los padres que necesitan saber la posición actual usan eso.

### El zoom del `v-model` llega tarde en `moveend` (2026-10-09)

vue-leaflet actualiza `update:zoom`/`update:center` desde **su propio** listener de `moveend`, envuelto en un debounce. Nuestro `@moveend` corre antes, así que si arma el bbox con `zoom.value` manda el zoom **anterior**. Con la rueda no se notaba (pasos de 1), pero un click en una burbuja del cluster salta varios niveles: el feed pedía H3 r7 sobre un bbox de zoom 16, ninguna celda r7 tenía su centro adentro y volvía `[]` — el mapa quedaba vacío. **Fix**: `onMoveEnd` lee bordes y zoom del mapa del evento (`event.target.getZoom()`), nunca del `v-model`.

### Race condition histórica: inicialización del center

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

El tipo de cada marker decide su ícono. Definido en `types/maps/base.ts`:

```ts
export type MarkerImageType = "subject" | "house" | "apartment" | "food" | "education"; // evoluciona

export interface MarkerData {
  id: string;
  lat: number;
  lon: number;
  imageType: MarkerImageType;
  label?: string;          // nombre — usado también en el popup del cluster
  categoryLabel?: string;
  address?: string;
  phone?: string;
  website?: string;
}
```

- **`subject`** = el inmueble que se está avaluando (marker propio, diferenciado de los comparables `house`/`apartment` y de los POIs `food`/`education`...).
- Los iconos son **componentes Lucide** (no SVGs en `public/icons/`). El mapeo `MarkerImageType → Component` vive en `constants/markerIcons.ts` como `Record<MarkerImageType, Component>` — p.ej. `house: MapPinHouse`, `apartment: Building`, `food: ChefHat`, `education: NotebookPen`.
- Para el cluster, `utils/markerIcon.ts` arma el `L.divIcon`: renderiza el componente de `markerIconMap` con `renderToElement` **una vez por tipo y estado** y cachea el HTML resultante (`htmlCache`); el resto de marcadores reusa el string. Casa y `subject` son pines con relleno navy (verde si están resaltados); apartamento, un círculo navy con el ícono; los POIs, un círculo del color de `POI_COLORS` con su ícono. `clusterIcon(n)` dibuja la burbuja navy con el conteo.
- `subject` sigue declarativo: `<l-icon>` con `<MapPinHouse>`. **No** se le pasa el `DivIcon` de `markerIcon` porque vue-leaflet tipa la prop `icon` de `<l-marker>` como `Icon` y `vue-tsc` lo rechaza.
- `MarkerData`/`MarkerImageType` son **una sola fuente de verdad** importada tanto por `MapUser` como por el padre que arma los markers.

### Gotchas de `l-icon` con componentes Vue

`<l-icon>` genera un `div` con estilos Leaflet visibles (borde, sombra, fondo). Para iconos Lucide (no pins tradicionales):

- Limpiar el contenedor: `class-name="!bg-transparent !border-0 !shadow-none"` en `<l-icon>`.
- **Anchor**: depende de la forma del icono. Para iconos cuadrados: `[w/2, h/2]` (centro). Para pins con punta abajo (como en MapView feed-mapa): `[w/2, h]` — e.g. `[12, 24]` para icono 24×24. Usar `[16, 32]` o valores fuera de bounds hace que el marcador se desplace.
- El componente Lucide necesita `color` explícito — dentro del div de Leaflet `currentColor` no resuelve a ningún color visible.
- **Lucide `Building` es stroke-only** — pasar `:fill` no tiene efecto. Para cambiar el fondo, envolver en un `div` con clase de background: `<div class="rounded-full bg-[#1e3a5f]"><Building :size="14" color="#FFF" /></div>`.

### Hover en ambos sentidos (feed-mapa)

- **Tarjeta → marcador**: `MapView` pasa `hoveredId` como prop; `MapUser` llama `cluster.highlight(id)`, que agranda el marcador (`setIcon`) o, si está dentro de una burbuja, le pone la clase `is-highlighted` a la burbuja (verde y escalada, en `main.css`). Se reaplica tras cada zoom o animación del cluster.
- **Marcador → tarjeta**: `MapUser` emite `markerHover(id | null)`; `MapView` resalta la tarjeta solo si ya está pintada en la lista.

## Cluster maker — `useMarkerCluster` (2026-10-09)

Desde el 2026-10-09 el cluster es genérico y agrupa **propiedades y POIs**, no solo POIs. Vive en `composables/map/useMarkerCluster.ts` y `MapUser` lo usa con todo lo que no es `subject`:

| Función | Qué hace |
|---|---|
| `attach(map)` | Mete el `MarkerClusterGroup` en el mapa cuando dispara `@ready` |
| `sync(markers)` | Compara con lo que ya hay por `id` y solo quita/agrega lo que cambió, en lote (`removeLayers`/`addLayers`) — no rearma el grupo |
| `highlight(id)` | Agranda el marcador; si está agrupado, resalta la burbuja que lo contiene (`getVisibleParent`) |
| `detach()` | Saca el grupo del mapa en `onUnmounted` |

Recibe callbacks opcionales (`MarkerClusterHandlers` en `types/maps/cluster.ts`): `popup(marker)`, `onClick(marker)`, `onHover(id)`. `MapUser` los conecta a `PoiPopup` y a los emits `markerClick`/`markerHover`. Opciones: `maxClusterRadius: 50`, `chunkedLoading`, `showCoverageOnHover: false` y `iconCreateFunction` con `clusterIcon`.

`@vue-leaflet` no trae componente de cluster: por eso lo agrupable es imperativo y solo `subject` queda en el template.

```ts
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { MarkerClusterGroup } = require("leaflet.markercluster");
import type {} from "leaflet.markercluster"; // tipos de L.MarkerClusterGroup
```

**`POI_COLORS` por `MarkerImageType`** — vive en `constants/poiColors.ts` (no inline en `MapUser.vue`), junto a `POI_BUCKET_LABELS` (labels en español por bucket):

```ts
// constants/poiColors.ts
export const POI_COLORS: Partial<Record<MarkerImageType, string>> = {
  food: "#f97316",       // naranja
  education: "#3b82f6",  // azul
  health: "#ef4444",     // rojo
  transport: "#8b5cf6",  // violeta
  commerce: "#eab308",   // amarillo
  poi: "#6b7280",        // gris (fallback)
};

export const POI_BUCKET_LABELS: Partial<Record<MarkerImageType, string>> = {
  food: "Comida", education: "Educación", health: "Salud",
  transport: "Transporte", commerce: "Comercio", poi: "Otros",
};
```

Se sacó de `MapUser.vue` para que un componente nuevo (`MapLegend.vue`) lo pueda reusar sin duplicar el objeto — ver [[frontend-poi-reachable]]. `MapUser` solo importa `POI_COLORS`.

**Tipos nuevos en `MarkerImageType`** (`types/maps/base.ts`): `health | transport | commerce | poi` — mapeados en `constants/markerIcons.ts` con `HeartPulse | Bus | ShoppingCart | MapPin`.

### Popup al click en markers del cluster

Cada marker con `label` recibe `bindPopup` con un `HTMLElement` renderizado desde **`PoiPopup.vue`** (`renderToElement(PoiPopup, { marker })`): nombre, categoría, dirección, teléfono y web, cada uno solo si existe. Reemplazó en 2026-10-09 a `buildPoiPopupHtml` + `escapeHtml`, que armaban el HTML como string: Vue ya escapa el texto. **El `website` solo se enlaza si empieza con `http(s)://`** — viene de OSM/Overpass y ni `encodeURI` (antes) ni Vue bloquean un `javascript:` en un `href`.

**CSS e imports:** webpack requiere imports explícitos (no CDN):
```ts
import "leaflet.markercluster/dist/MarkerCluster.css";
```

`MarkerCluster.Default.css` ya no se importa: las burbujas las dibuja `clusterIcon`.

`shims-vue.d.ts` necesita:
```ts
declare module '*.css';
declare module 'leaflet.markercluster';
```

**ESLint:** `defineModel` es una macro de Vue 3.4 — añadir a `.eslintrc.js` globals:
```js
globals: { defineModel: "readonly" }
```

`onUnmounted`: `cluster.detach()` para limpiar.

## D3 como capa plug-and-play

D3 sobre el mapa (heatmaps, densidad, choropleth) **no va en la view ni dentro de `MapUser`**. Va en un componente/composable dedicado que **consume la instancia Leaflet** que `MapUser` expone (vía `@ready`/`defineExpose`):
- La mecánica D3↔Leaflet (proyectar con `latLngToLayerPoint`, redibujar en `zoomend`/`moveend`, pane SVG) necesita la instancia → vive pegada a ella, no en la view.
- La **data** a visualizar baja desde la view por props (mismo principio data-driven que los markers).
- `MapUser` no importa D3 → solo entra al bundle donde se use la capa. Markers y overlay D3 son panes distintos, conviven sin pisarse.

Ver [[adr-mapbox-geocoding-leaflet-rendering]] para la decisión de stack (Leaflet+D3).

## Estado (2026-06-20)

- Vue 3.5 upgrade completado — `defineModel` y `useTemplateRef` funcionan.
- Iconos migrados a Lucide (`markerIconMap` en `constants/markerIcons.ts`).
- `internalCenter` pattern implementado — `defineModel center` ya no va directo a `l-map`.
- `leaflet.markercluster` integrado para POI markers (split imperativo/declarativo).
- Markers del cluster tienen `bindPopup` con info del POI (nombre/categoría/dirección/teléfono/website), escapada con `escapeHtml`.
- `POI_COLORS`/`POI_BUCKET_LABELS` centralizados en `constants/poiColors.ts`; nuevo componente reusable `MapLegend.vue`.
- `MapUser` usado en `DevPlaygroundView` (AVM), `MapView` (feed-mapa) y `NearbyPlaces` (dentro de `PropertyDetailView`, POI section).

**Update 2026-10-09:** cluster genérico con iconos lucide para propiedades y POIs (`useMarkerCluster`), `PoiPopup`, emits `markerClick`/`markerHover`, zoom leído del mapa en `moveend`. El feed-mapa pinta todo el bbox ([[adr-feed-map-whole-bbox-cluster]]). `MapUser` se usa en `AvmView`, `MapView` y `NearbyPlaces`.

## Segundo mapa: `NeighborhoodMap.vue` del panel admin (2026-10-04)

El panel de barrios ([[frontend-admin-panel]]) usa un componente propio y no `MapUser`, que está pensado para marcadores con cluster, tiene zoom mínimo 14 y no expone `fitBounds`. `NeighborhoodMap` es igual de tonto, pero dibuja polígonos:

- `LMap` + tiles de OSM + dos `LGeoJson`: los vecinos abajo (gris, tooltip con el nombre) y el barrio elegido encima (verde marca).
- **Vista fija**: sin controles de zoom, arrastre, rueda ni teclado. El encuadre lo decide el barrio: `fitBounds` sobre su geometría con 24 px de padding, o el centroide con zoom 15 si no tiene geometría.
- Tras encuadrar emite `bounds` con `[oeste, sur, este, norte]` de `map.getBounds()`, que es el bbox con el que el panel pide los vecinos.
- El `center` solo se usa para arrancar y el `watch` observa geometría, latitud y longitud como fuentes separadas. Con `:center="[lat, lon]"` inline cada render generaba un array nuevo y se formaba un ciclo: vecinos → re-render → reencuadre → vecinos.

## Claims

- `MapUser.vue` usa `@vue-leaflet/vue-leaflet` (`LMap`, `LTileLayer`, `LMarker`, `LIcon`) ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- El padre debe pasar `:markers="marker ? [marker] : []"` cuando el marker puede ser `null` ([views/avm/AvmView.vue](frontend/src/views/avm/AvmView.vue)).
- `zoom` es two-way vía `defineModel` + `v-model:zoom` en `<l-map>` — requiere Vue 3.4+ ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- `center` usa `internalCenter` como intermediario — Leaflet emite `LatLng` objects en `update:center`, no tuples; vincular `defineModel center` directo a `<l-map>` causa crash `Invalid LatLng object: (undefined, undefined)` ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- `internalCenter` se inicializa con `center.value ?? [4.681414, -74.046864]`; un `watch(center, ...)` permite que el padre mueva el mapa programáticamente ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- vue-leaflet registra su watcher de `center` dentro de un `onMounted` async — actualizar `center.value` desde el padre en `onMounted` crea una race condition; el fix es inicializar el ref síncronamente en script setup ([views/properties/feed/MapView.vue](frontend/src/views/properties/feed/MapView.vue)).
- Todos los markers salvo `subject` (propiedades y POIs) se renderizan con `useMarkerCluster`; `subject` es un `<l-marker>` declarativo ([components/map/MapUser.vue:18-24](frontend/src/components/map/MapUser.vue#L18-L24), [:70-77](frontend/src/components/map/MapUser.vue#L70-L77)).
- `require("leaflet.markercluster")` en vez de `import` — webpack no adjunta el plugin al namespace `L` con ES import ([composables/map/useMarkerCluster.ts:4](frontend/src/composables/map/useMarkerCluster.ts#L4)).
- El grupo está tipado como `L.MarkerClusterGroup` vía `import type {} from "leaflet.markercluster"` ([composables/map/useMarkerCluster.ts:21](frontend/src/composables/map/useMarkerCluster.ts#L21)).
- El CSS del cluster se importa explícito y solo `MarkerCluster.css`; las burbujas las dibuja `clusterIcon` ([composables/map/useMarkerCluster.ts:2](frontend/src/composables/map/useMarkerCluster.ts#L2), [utils/markerIcon.ts:65](frontend/src/utils/markerIcon.ts#L65)).
- `shims-vue.d.ts` necesita `declare module '*.css'` y `declare module 'leaflet.markercluster'` para que TypeScript acepte esos imports ([shims-vue.d.ts](frontend/src/shims-vue.d.ts)).
- `defineModel` añadido a `.eslintrc.js` globals (`"readonly"`) — macro Vue 3.4 no reconocida sin esto ([.eslintrc.js](frontend/.eslintrc.js)).
- `v-model` no acepta TypeScript `as` casts (inválido como LHS) — usar un ref correctamente tipado en su lugar.
- `MapUser` expone una prop `markers: MarkerData[]` **y** un `<slot>` para capas extra, y emite `bbox`, `markerClick` y `markerHover` ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- Los iconos de marker son componentes Lucide resueltos por `markerIconMap`; `markerIcon` los renderiza una vez por tipo y estado y cachea el HTML en `htmlCache` ([utils/markerIcon.ts:17](frontend/src/utils/markerIcon.ts#L17), [constants/markerIcons.ts](frontend/src/constants/markerIcons.ts)).
- El `<l-icon>` del `subject` usa `class-name=""` y renderiza `<MapPinHouse>`; no recibe un `DivIcon` porque vue-leaflet tipa `icon` como `Icon` ([components/map/MapUser.vue:22](frontend/src/components/map/MapUser.vue#L22)).
- Anchor para pins con punta: `[w/2, h]` (e.g. `[12, 24]`); para iconos circulares, el centro `[w/2, h/2]` ([utils/markerIcon.ts](frontend/src/utils/markerIcon.ts)).
- Lucide `Building` es stroke-only — `:fill` no tiene efecto; `markerIcon` lo envuelve en un círculo con fondo ([utils/markerIcon.ts](frontend/src/utils/markerIcon.ts)).
- `MarkerData`, `MarkerImageType` y `Bbox` viven en `types/maps/base.ts` ([types/maps/base.ts](frontend/src/types/maps/base.ts)).
- El CSS de Leaflet se carga vía `<link>` en `public/index.html`, no por import ([public/index.html:11](frontend/public/index.html#L11)).
- `POI_COLORS` y `POI_BUCKET_LABELS` viven en `constants/poiColors.ts`, no inline en `MapUser.vue` — reusados por `MapLegend.vue` ([constants/poiColors.ts](frontend/src/constants/poiColors.ts)).
- Cada marker del cluster con `label` definido recibe `bindPopup` con `PoiPopup` renderizado por `renderToElement` ([components/map/MapUser.vue](frontend/src/components/map/MapUser.vue)).
- `PoiPopup.vue` solo enlaza el `website` si empieza con `http://` o `https://` ([components/map/PoiPopup.vue:25-26](frontend/src/components/map/PoiPopup.vue#L25-L26)).
- `MapLegend.vue` (`components/map/`) es un componente sin estado que itera `POI_COLORS`/`POI_BUCKET_LABELS` — pensado para reusarse en `AvmView` además de `NearbyPlaces` ([components/map/MapLegend.vue](frontend/src/components/map/MapLegend.vue)).
- `useMarkerCluster.sync` solo quita y agrega los markers que cambiaron (por `id`), con `removeLayers`/`addLayers` en lote ([composables/map/useMarkerCluster.ts:47-66](frontend/src/composables/map/useMarkerCluster.ts#L47-L66)).
- `useMarkerCluster.highlight` resalta la burbuja que contiene al marker con la clase `is-highlighted` cuando el marker está agrupado ([composables/map/useMarkerCluster.ts:76-79](frontend/src/composables/map/useMarkerCluster.ts#L76-L79), [main.css:34](frontend/src/main.css#L34)).
- `onMoveEnd` arma el bbox con `map.getZoom()` del evento, no con el `zoom` del `v-model` ([components/map/MapUser.vue:107](frontend/src/components/map/MapUser.vue#L107)).
- `NeighborhoodMap.vue` desactiva zoom y arrastre en `MAP_OPTIONS` y encuadra con `fitBounds` sobre la geometría del barrio ([NeighborhoodMap.vue:49](frontend/src/components/admin/catalog/neighborhoods/widgets/NeighborhoodMap.vue#L49), [:98](frontend/src/components/admin/catalog/neighborhoods/widgets/NeighborhoodMap.vue#L98)).
- `NeighborhoodMap.vue` emite `bounds` como `[oeste, sur, este, norte]` desde `map.getBounds()` ([NeighborhoodMap.vue:106](frontend/src/components/admin/catalog/neighborhoods/widgets/NeighborhoodMap.vue#L106)).
- El `watch` de `NeighborhoodMap.vue` observa `geometry`, `center[0]` y `center[1]` como fuentes separadas ([NeighborhoodMap.vue:116](frontend/src/components/admin/catalog/neighborhoods/widgets/NeighborhoodMap.vue#L116)).
