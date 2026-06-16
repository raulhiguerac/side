---
title: Flujo POIs alcanzables — PropertyDetailView
status: stable
last-verified: 2026-06-15
owners: [frontend]
related:
  - "[[frontend-map-component]]"
  - "[[frontend-architecture]]"
  - "[[catalog-service-ors]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[adr-isochrone-ors-h3]]"
sources:
  - ../../sources/frontend/2026-06-15-poi-detail-view-mapuser-cluster.md
---

## TL;DR

`PropertyDetailView` incluye una sección "Cerca del lugar" que muestra los POIs alcanzables desde la propiedad según 3 perfiles de transporte (pie/bici/carro) y 3 rangos temporales (5/10/15 min). Un solo POST al backend devuelve los 9 resultados; el frontend filtra, agrupa por categoría y renderiza isocronas + markers clusterizados en el mapa.

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
```

`CATEGORY_PRIORITY`: prioridad numérica por categoría OSM (hospital=1, school=2, restaurant=3, supermarket=4, bus=5...). `CATEGORY_META`: mapea categoría OSM → `{ label: string (español), icon: Component (Lucide) }`.

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

## PropertyDetailView — sección "Cerca del lugar"

### Profile chips
3 botones que escriben `activeProfile`. El chip activo tiene `bg-brand-primary text-white`. La descripción del perfil activo aparece debajo como texto `xs text-brand-muted`.

### Acordeón por rango
- Un acordeón por cada `RangeGroup` del perfil activo (3 en total).
- Default open: 5 min (`openRange = ref<number>(5)`).
- Click en header: toggle (`openRange === range.minutes ? -1 : range.minutes`).
- Header: dot de color + `X min` + `N lugares` + chevron.
- Body: grid 2 cols, máx 8 cards, cada card = categoría (icon + label) + hasta 2 nombres de POI.

### Mapa
- `MapUser` con `:min-zoom="12"` y `v-model:center="mapCenterCoords"`.
- `mapCenterCoords: Ref<[number, number] | undefined>` — ref local inicializado en `onMounted` desde `property.location` (no el computed `mapCenter` del composable, para evitar cast inválido en `v-model`).
- **Isocronas** en slot: `[...groupedByRange].reverse()` para que el polígono de 15 min (más grande) quede debajo, 5 min (más pequeño) encima. `fill-opacity=0.3`, sin borde (`opacity=0`, `weight=0`).
- **POI markers**: `poiMarkers` computed — itera todos los grupos del perfil activo, deduplica por `${lat},${lon}`, asigna `imageType` via `CATEGORY_TO_MARKER`.

### `CATEGORY_TO_MARKER`
```ts
{ school/kindergarten/college/university → "education",
  hospital/clinic/doctor/dentist/pharmacy → "health",
  restaurant/cafe/fast_food/bakery → "food",
  supermarket/convenience → "commerce",
  bus_station/platform/stop_position → "transport" }
// fallback: "poi"
```

### Subject marker
`mapCenterCoords` genera un marker tipo `"subject"` (el pin de la propiedad misma) que siempre aparece en el mapa independientemente del perfil activo.

## Open items

- Panel izquierdo muestra `range.count` (total backend); mapa muestra markers filtrados/deduplicados — los números no coinciden. Pendiente decidir si mostrar conteo filtrado, dual, o ninguno.
- Hover tooltips en markers del cluster (`.bindTooltip`) — requiere añadir `name` a `MarkerData`.
- `PropertyDetailView` usa mock hardcodeado — pendiente conectar a `GET /v1/properties/{id}`.
- Refactor pendiente de la sección POI (señalado por el autor).

## Claims

- `useReachablePois` hace un único `POST /v1/geo-resolution/reachable-pois` con `range_seconds: [300, 600, 900]` y los 3 perfiles — 9 resultados en una sola llamada ([composables/pois/useReachablePois.ts](frontend/src/composables/pois/useReachablePois.ts)).
- `groupedByRange` filtra por `activeProfile` y agrupa por `CATEGORY_META[category].label` — máx 8 grupos × 2 POIs; ordena por `CATEGORY_PRIORITY` ([composables/pois/useReachablePois.ts](frontend/src/composables/pois/useReachablePois.ts)).
- POIs donde `name === category` se filtran — son nodos OSM sin nombre real ([composables/pois/useReachablePois.ts:65](frontend/src/composables/pois/useReachablePois.ts#L65)).
- `mapCenterCoords` es un `ref<[number, number] | undefined>()` local en `PropertyDetailView`, no el `mapCenter` del composable — evita cast `as [number, number]` inválido en `v-model` ([views/properties/detail/PropertyDetailView.vue](frontend/src/views/properties/detail/PropertyDetailView.vue)).
- Las isocronas en el slot de `MapUser` se renderizan con `[...groupedByRange].reverse()` para que el polígono mayor (15 min) quede debajo del menor (5 min) ([views/properties/detail/PropertyDetailView.vue](frontend/src/views/properties/detail/PropertyDetailView.vue)).
- `poiMarkers` deduplica por `\`${lat},${lon}\`` — evita markers solapados cuando el mismo POI aparece en varios rangos ([views/properties/detail/PropertyDetailView.vue](frontend/src/views/properties/detail/PropertyDetailView.vue)).
- `types/pois.ts` contiene `OrsProfile`, `GeoJsonPolygon`, `ReachablePoiItem`, `ReachablePoisResult`, `RangeGroup`, `CATEGORY_PRIORITY`, `CATEGORY_META`, `PRIORITY_CATEGORIES` ([types/pois.ts](frontend/src/types/pois.ts)).
