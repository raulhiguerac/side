---
title: Flujo POIs alcanzables — NearbyPlaces
status: stable
last-verified: 2026-06-20
owners: [frontend]
related:
  - "[[frontend-map-component]]"
  - "[[frontend-architecture]]"
  - "[[catalog-service-ors]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[adr-isochrone-ors-h3]]"
sources:
  - ../../sources/frontend/2026-06-15-poi-detail-view-mapuser-cluster.md
  - ../../sources/frontend/2026-06-20-property-detail-view-refactor.md
---

## TL;DR

`NearbyPlaces.vue` (`components/properties/`) es el componente autocontenido que muestra los POIs alcanzables desde una propiedad: 3 perfiles de transporte (pie/bici/carro) × 3 rangos temporales (5/10/15 min). Recibe `lat`/`lon`/`propertyId` como props y resuelve todo internamente — la view padre (`PropertyDetailView`) no sabe nada de POIs, perfiles ni mapa.

## Ownership — por qué el composable vive en el componente, no en la view

A diferencia de otros datos de la propiedad (que `PropertyDetailView` resuelve via `usePropertyDetail` y pasa hacia abajo ya computados), `useReachablePois` depende de un fetch async que solo puede arrancar cuando la propiedad ya cargó (necesita `lat`/`lon`/`propertyId`). En vez de que la view orqueste ese timing, `NearbyPlaces` es dueño del composable y llama `loadPois(lat, lon, propertyId)` en su propio `onMounted` — queda autocontenido, la view solo lo monta con 3 props cuando `property.location` existe.

## Tipos — `types/pois.ts`

```ts
export type OrsProfile = "foot-walking" | "cycling-regular" | "driving-car";

export interface GeoJsonPolygon {
  type: "Polygon";
  coordinates: number[][][];          // matches backend GeoJsonPolygon schema
}

export interface ReachablePoiItem {
  name: string; category: string | null;
  latitude: number; longitude: number;
  full_address: string | null; phone: string | null; website: string | null;
}

export interface ReachablePoisResult {
  profile: OrsProfile; range: number | null;
  isochrone: GeoJsonPolygon | null;
  pois: ReachablePoiItem[];
  error: string | null;
}

export interface RangeGroup {
  profile: OrsProfile; minutes: number; seconds: number;
  dot: string; count: number;
  pois: ReachablePoiItem[]; isochrone: GeoJsonPolygon | null;
}

export interface CategoryMeta {
  label: string;
  icon: Component;
  bucket: MarkerImageType;   // single source of truth categoría OSM → bucket del mapa
}
```

`CATEGORY_PRIORITY`: prioridad numérica por categoría OSM (hospital=1, school=2, restaurant=3, supermarket=4, bus=5...). `CATEGORY_META`: mapea categoría OSM → `{ label: string (español), icon: Component (Lucide), bucket: MarkerImageType }` — el campo `bucket` es la fuente única para resolver el color del marker en el mapa (ver [[frontend-map-component]]); antes existía un objeto separado `CATEGORY_TO_MARKER` en `NearbyPlaces.vue` que duplicaba las mismas 18 keys, eliminado.

## Composable `useReachablePois` (`composables/pois/useReachablePois.ts`)

Un solo POST con todos los rangos y perfiles:

```ts
POST /v1/geo-resolution/reachable-pois
{
  lat, lon, property_id,
  range_seconds: [300, 600, 900],
  profile: ["foot-walking", "cycling-regular", "driving-car"]
}
// response: 9 ReachablePoisResult (3 rangos × 3 perfiles)
```

**Estado expuesto:**
- `activeProfile: Ref<OrsProfile>` — perfil activo (cambia al pulsar chip).
- `ranges: Ref<RangeGroup[]>` — todos los resultados crudos (9 entradas).
- `loading: Ref<boolean>`.
- `profiles: ProfileOption[]` — array constante con los 3 perfiles + icono Lucide + descripción.
- `groupedByRange: ComputedRef<RangeWithGroups[]>` — filtra `ranges` por `activeProfile`, agrupa POIs por categoría (ver abajo).

**`groupByCategory`:**
1. Filtra POIs cuya categoría no está en `CATEGORY_META` (no relevantes).
2. Filtra POIs donde `name === category` (nodos OSM sin nombre real).
3. Agrupa por `CATEGORY_META[category].label` — máx 2 POIs por grupo.
4. Ordena grupos por `CATEGORY_PRIORITY`.

**`ISOCHRONE_COLORS`:** `{ 5: "#ef4444", 10: "#22c55e", 15: "#6366f1" }` (rojo / verde brand / índigo).
**`DOT_BY_SECONDS`:** `{ 300: "bg-red-500", 600: "bg-green-500", 900: "bg-indigo-500" }`.

## `NearbyPlaces.vue` — sección "Cerca del lugar"

### Profile chips
3 botones que escriben `activeProfile`. El chip activo tiene `bg-brand-primary text-white`. La descripción del perfil activo aparece debajo como texto `xs text-brand-muted`. En mobile (`flex-col`, sin `md:`) los chips usan `flex-wrap`.

### Acordeón por rango
- Un acordeón por cada `RangeGroup` del perfil activo (3 en total).
- Default open: 5 min (`openRange = ref<number>(5)`).
- Click en header: toggle (`openRange === range.minutes ? -1 : range.minutes`).
- Header: dot de color + `X min` + `N lugares` + chevron.
- Body: grid 2 cols, máx 8 cards, cada card = categoría (icon + label) + hasta 2 nombres de POI.

### Leyenda de categorías (`MapLegend`)
Componente reusable (`components/map/MapLegend.vue`) en la misma fila que los chips de perfil, alineado a la columna donde después aparece el mapa (no overlay sobre los tiles). Itera `POI_COLORS`/`POI_BUCKET_LABELS` de `constants/poiColors.ts` — mismo source of truth que usa el cluster del mapa, pensado para reusarse también en `AvmView` (pendiente de conectar ahí).

### Mapa
- `MapUser` con `:min-zoom="12"` y `v-model:center="mapCenterCoords"`.
- `mapCenterCoords: Ref<[number, number] | undefined>` — ref local en `NearbyPlaces`, inicializado en el propio `script setup` desde los props `lat`/`lon` (no un computed del composable, para evitar cast inválido en `v-model`).
- **Isocronas** en slot: `[...groupedByRange].reverse()` para que el polígono de 15 min (más grande) quede debajo, 5 min (más pequeño) encima. `fill-opacity=0.3`, sin borde (`opacity=0`, `weight=0`).
- **POI markers**: `poiMarkers` computed — itera todos los grupos del perfil activo, deduplica por `${lat},${lon}`, asigna `imageType` via `CATEGORY_META[poi.category ?? ""]?.bucket ?? "poi"`, y arma `label`/`categoryLabel`/`address`/`phone`/`website` para el popup del marker (ver [[frontend-map-component]]).

### Subject marker
`mapCenterCoords` genera un marker tipo `"subject"` (el pin de la propiedad misma) que siempre aparece en el mapa independientemente del perfil activo.

### Responsive
Tanto la fila de chips+leyenda como la fila de POIs+mapa son `flex-col` por default y `md:flex-row` desde tablet. En mobile el mapa va arriba y los POIs abajo (`order-1 md:order-2` en la columna del mapa, `order-2 md:order-1` en la del acordeón) — en desktop el orden visual vuelve a POIs-izquierda/mapa-derecha.

## Open items

- Panel izquierdo muestra `range.count` (total backend); mapa muestra markers filtrados/deduplicados — los números no coinciden. Pendiente decidir si mostrar conteo filtrado, dual, o ninguno.
- `MapLegend` está implementado pero no conectado en `AvmView` todavía (mencionado como next step, no hecho).
- `location-label` (en `PropertyOverview`, fuera de este componente) solo resuelve barrio, no ciudad.

## Claims

- `NearbyPlaces.vue` recibe `lat`, `lon`, `propertyId` como props y llama `loadPois` en su propio `onMounted` — no depende de que la view padre orqueste el timing del fetch ([components/properties/NearbyPlaces.vue](frontend/src/components/properties/NearbyPlaces.vue)).
- `useReachablePois` hace un único `POST /v1/geo-resolution/reachable-pois` con `range_seconds: [300, 600, 900]` y los 3 perfiles — 9 resultados en una sola llamada ([composables/pois/useReachablePois.ts](frontend/src/composables/pois/useReachablePois.ts)).
- `groupedByRange` filtra por `activeProfile` y agrupa por `CATEGORY_META[category].label` — máx 8 grupos × 2 POIs; ordena por `CATEGORY_PRIORITY` ([composables/pois/useReachablePois.ts](frontend/src/composables/pois/useReachablePois.ts)).
- POIs donde `name === category` se filtran — son nodos OSM sin nombre real ([composables/pois/useReachablePois.ts](frontend/src/composables/pois/useReachablePois.ts)).
- `CategoryMeta` tiene un campo `bucket: MarkerImageType` — única fuente de verdad categoría OSM → color de marker, reemplaza al objeto `CATEGORY_TO_MARKER` que existía duplicado en el componente ([types/pois.ts](frontend/src/types/pois.ts)).
- `mapCenterCoords` es un `ref<[number, number] | undefined>()` local en `NearbyPlaces`, no un computed del composable — evita cast `as [number, number]` inválido en `v-model` ([components/properties/NearbyPlaces.vue](frontend/src/components/properties/NearbyPlaces.vue)).
- Las isocronas en el slot de `MapUser` se renderizan con `[...groupedByRange].reverse()` para que el polígono mayor (15 min) quede debajo del menor (5 min) ([components/properties/NearbyPlaces.vue](frontend/src/components/properties/NearbyPlaces.vue)).
- `poiMarkers` deduplica por `\`${lat},${lon}\`` — evita markers solapados cuando el mismo POI aparece en varios rangos ([components/properties/NearbyPlaces.vue](frontend/src/components/properties/NearbyPlaces.vue)).
- `types/pois.ts` contiene `OrsProfile`, `GeoJsonPolygon`, `ReachablePoiItem`, `ReachablePoisResult`, `RangeGroup`, `CATEGORY_PRIORITY`, `CATEGORY_META`, `PRIORITY_CATEGORIES` ([types/pois.ts](frontend/src/types/pois.ts)).
- `MapLegend.vue` (`components/map/`) itera `POI_COLORS`/`POI_BUCKET_LABELS` de `constants/poiColors.ts` — reusable, sin estado propio ([components/map/MapLegend.vue](frontend/src/components/map/MapLegend.vue)).
