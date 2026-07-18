---
title: ADR-0003 — Mapbox solo para geocoding, Leaflet+D3 para render
status: stable
last-verified: 2026-07-15
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[frontend-map-component]]"
  - "[[adr-mapbox-frontend-only]]"
  - "[[adr-gmaps-places-geocoding]]"
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md, ../../../sources/frontend/2026-05-27-gmaps-places-avm-form.md, ../../../sources/frontend/2026-05-28-avm-form-split-and-dumb-map.md]
decision-date: 2026-05-21
decision-status: superseded-partial
---

> ⚠️ **Supersedida parcialmente por [[adr-gmaps-places-geocoding]] (2026-05-27)**: la mitad de geocoding (Mapbox → `address→lat/lon`) fue reemplazada por Google Maps Places API (New). La mitad de rendering (Leaflet+D3) sigue vigente.

# ADR-0003 — Mapbox solo para geocoding, Leaflet+D3 para render

## Contexto

El frontend necesita dos capacidades distintas de mapa:

1. **Geocoding**: el usuario tipea una dirección → autocomplete + resolución a `(lat, lon)` para guardarse en el listing. Esto necesita un provider con dataset global, actualizado y autocomplete UX.
2. **Renderizado de mapas**: mostrar la propiedad/listings en un mapa, dibujar polígonos de barrios, heatmaps de precio (futuro), overlays de POIs (futuro).

Los proveedores tienen trade-offs distintos para cada uno:

| Provider | Geocoding | Rendering | Precio | Restricciones |
|---|---|---|---|---|
| Mapbox | ✅ excelente, autocomplete nativo | ✅ tiles + GL | Free tier limitado, paid por arriba | Lock-in si usas Mapbox Studio styling |
| Leaflet | ❌ (no incluye) | ✅ + plugin ecosystem maduro | gratis OSS | Necesita un tile provider (OSM gratis, Mapbox tiles, etc.) |
| Google Maps | ✅ excelente | ✅ | precios punitivos para volumen, requires billing key | Branding obligatorio |
| OpenStreetMap (Nominatim) | ⚠ funciona, rate-limit estricto | ✅ tiles OSM | gratis | No apto para producción sin self-host |

## Decisión

**Split por responsabilidad:**

- **Mapbox SDK en frontend** solo para forward geocoding (`address → lat/lon`). Autocomplete y preview en mapa pequeño al publicar listing.
- **Leaflet + `@vue-leaflet/vue-leaflet`** para todo el renderizado de mapas (página de propiedad, futuro heatmap, futuro mapa de búsqueda).
- **D3.js** para overlays/visualizations customizadas sobre Leaflet (heatmaps con gradient, anotaciones de precio, escalas de color).
- **Reverse geocoding** (`lat/lon → barrio`) **no usa Mapbox** — lo hace `catalog-service` contra polígonos IDECA locales. Ver [[adr-mapbox-frontend-only]] (cross-service).

## Alternativas consideradas

- **Todo Mapbox** (geocoding + rendering): UX integrada, menor surface técnico. Pero costos suben rápido con volumen + lock-in a Mapbox Studio styling.
- **Todo Leaflet + Nominatim** para geocoding: 100% gratis pero Nominatim no es apto para producción (rate-limit) y autocomplete UX hay que construirla.
- **Todo Google Maps**: excelente UX pero precios altos para Colombia y branding obligatorio.
- **Mapbox solo geocoding, Mapbox GL para render**: redunda en costo Mapbox alto cuando los renders sean masivos.

## Consecuencias

- ✅ **Costo controlado**: Mapbox solo se paga por geocode requests (mucho menos volumen que tile requests).
- ✅ **Libertad visual**: Leaflet + D3 permite cualquier visualization customizada (heatmaps, polygons, charts overlay).
- ✅ **Reverse no depende de proveedor externo** — catalog-service usa polígonos locales (IDECA), zero costo per-request.
- ✅ **Bundle size**: solo importamos los pieces de Mapbox SDK que necesitamos (geocoder), no el full GL.
- ❌ **Dos librerías de mapa** en el código (Mapbox SDK + Leaflet) — más superficie técnica.
- ❌ **Tiles**: Leaflet necesita un tile provider. Default OSM funciona pero las tiles no son las mejores estéticamente. Cuando importe la estética, evaluar Mapbox tiles vía Leaflet plugin (vuelve a costo pero acotado).
- ❌ **D3 + Leaflet**: integrar D3 con Leaflet requiere truco específico (D3 dibuja en SVG layer pero hay que sincronizar projection). Curva de aprendizaje.

## Integration pattern D3 ↔ Leaflet (definido 2026-05-28)

D3 sobre el mapa va como **capa plug-and-play**, no dentro del componente de mapa ni en la view:
- El componente de mapa ([[frontend-map-component]]) es dumb y **expone su instancia Leaflet** (vía `@ready`/`defineExpose`).
- Un componente/composable D3 **dedicado** consume esa instancia y posee la mecánica (proyectar con `latLngToLayerPoint`, pane SVG, redibujar en `zoomend`/`moveend`).
- La **data** a visualizar baja desde la view por props (data-driven, igual que los markers).
- El mapa no importa D3 → solo entra al bundle donde se use la capa. Markers (capa Leaflet) y overlay D3 (pane SVG) conviven sin pisarse.

Iconos de marker: SVGs en `public/icons/<imageType>.svg` (no `src/assets/`, porque un `:src` dinámico no resuelve por el bundler). Detalle en [[frontend-map-component]].

## Estado en código

- `leaflet` y `@vue-leaflet/vue-leaflet` están en **devDependencies** del `package.json` — **probable bug**, deberían estar en `dependencies` si se usan en runtime. Verificar al refactorear.
- `MapUser.vue` es el componente de mapa actual — dumb/reusable, documentado en [[frontend-map-component]]. Ya no es un componente huérfano: se usa en `MapView.vue` (feed-mapa), `AvmView.vue` y `NearbyPlaces.vue`.
- Mapbox SDK no está en `dependencies` del `package.json` al 2026-05-21 — habrá que agregarlo cuando se implemente el autocomplete de address.
- `vue-google-autocomplete` está en deps — **probable zombie** de cuando se evaluó Google Maps; se eliminará en cleanup.

## Open items

- Mover `leaflet`/`@vue-leaflet/vue-leaflet` a `dependencies`.
- Eliminar `vue-google-autocomplete` si no se usa.
- Decidir tile provider en producción (OSM gratis vs Mapbox vía Leaflet plugin).
- Pattern D3 ↔ Leaflet **definido** (ver sección arriba); falta **implementarlo** en el primer heatmap real.

## Claims

- `leaflet` (^1.9.4) y `@vue-leaflet/vue-leaflet` (^0.10.1) siguen en `devDependencies` del `package.json` ([package.json:51](frontend/package.json#L51), [package.json:40](frontend/package.json#L40)) — el "probable bug" de Open Items sigue sin resolver.
- `vue-google-autocomplete` está en `dependencies` (^1.1.4) — zombie confirmado: Google Places (New) vía `@googlemaps/js-api-loader` ya lo reemplazó ([package.json:28](frontend/package.json#L28)).
- Mapbox SDK **NO** está en `package.json` — confirmado que sigue sin agregarse (Google Places (New) cubrió el forward geocoding en su lugar, ver [[adr-gmaps-places-geocoding]]).
- `MapUser.vue` ya no es un componente huérfano — se usa activamente en `MapView.vue`, `AvmView.vue` y `NearbyPlaces.vue`.
- D3.js sigue sin instalarse ni usarse en el repo (cero referencias en `package.json`/`src/`) — el pattern D3↔Leaflet sigue definido pero no implementado.
- Reverse geocoding lo hace `catalog-service` via `/v1/geo-resolution/by-coordinates`, sin proveedor externo ([[adr-mapbox-frontend-only]]).
