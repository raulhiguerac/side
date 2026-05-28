---
title: ADR-0003 — Mapbox solo para geocoding, Leaflet+D3 para render
status: stable
last-verified: 2026-05-27
owners: [frontend]
related: [[frontend]], [[frontend-architecture]], [[adr-mapbox-frontend-only]], [[adr-gmaps-places-geocoding]]
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md, ../../../sources/frontend/2026-05-27-gmaps-places-avm-form.md]
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

## Estado en código

- `leaflet` y `@vue-leaflet/vue-leaflet` están en **devDependencies** del `package.json` — **probable bug**, deberían estar en `dependencies` si se usan en runtime. Verificar al refactorear.
- `MapUser.vue` es el componente de mapa actual (no leído en detalle).
- Mapbox SDK no está en `dependencies` del `package.json` al 2026-05-21 — habrá que agregarlo cuando se implemente el autocomplete de address.
- `vue-google-autocomplete` está en deps — **probable zombie** de cuando se evaluó Google Maps; se eliminará en cleanup.

## Open items

- Mover `leaflet`/`@vue-leaflet/vue-leaflet` a `dependencies`.
- Eliminar `vue-google-autocomplete` si no se usa.
- Decidir tile provider en producción (OSM gratis vs Mapbox vía Leaflet plugin).
- Documentar el integration pattern D3 ↔ Leaflet cuando se implemente el primer heatmap.

## Claims

- `leaflet` (^1.9.4) y `@vue-leaflet/vue-leaflet` (^0.10.1) están en `devDependencies` del `package.json` ([package.json:32-33](frontend/package.json#L32-L33), [package.json:43](frontend/package.json#L43)).
- `vue-google-autocomplete` está en `dependencies` (^1.1.4) — origen residual a confirmar ([package.json:23](frontend/package.json#L23)).
- Mapbox SDK **NO** está en `package.json` al 2026-05-21 — pendiente agregar cuando se implemente el autocomplete.
- `MapUser.vue` existe en `components/map/` pero su uso no aparece en las views revisadas en este pase del wiki.
- Reverse geocoding lo hace `catalog-service` via `/v1/geo-resolution/by-coordinates`, sin proveedor externo ([[adr-mapbox-frontend-only]]).
