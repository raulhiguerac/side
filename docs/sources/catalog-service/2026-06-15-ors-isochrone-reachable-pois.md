---
title: ORS isochrone integration — reachable-pois endpoint
captured-from: conversation
captured-on: 2026-06-15
participants: [raul, claude]
---

## Context

Implementación del endpoint `POST /v1/geo-resolution/reachable-pois` en catalog-service. Dado lat/lon + rangos en segundos + perfiles de transporte, devuelve los POIs alcanzables usando isócronas de ORS y lookup H3.

## Key conclusions

- **Stack**: `OrsRoutingClient` (httpx async) → `OrsRoutingAdapter` → `RoutingGateway` (Protocol) → `ResolveIsochroneUseCase`.
- **Parallel gather**: el cliente lanza un `asyncio.gather` con una coroutine por perfil (`foot-walking`, `driving-car`, `cycling-regular`). Cada resultado incluye `profile` para identificar errores por perfil sin bloquear los demás.
- **ORS endpoint**: `POST {ORS_URL}/v2/isochrones/{profile}` con body `{"locations": [[lon, lat]], "range": [seconds]}`. ORS usa lon-lat (invertido vs Leaflet). En Docker el DNS es `router:8082/ors` (nombre del servicio en docker-compose).
- **H3 lookup**: `h3.polygon_to_cells(h3.LatLngPoly([(lat, lng) for lng, lat in exterior]), res=settings.H3_RESOLUTION)` sobre el anillo exterior (`coordinates[0]`). Resolución r9 — misma que el sistema POI existente.
- **1 query para N isócronas**: se acumulan todas las celdas de todos los perfiles en `all_cells`, una sola llamada `get_by_h3_cells(h3_cells=all_cells)`, luego groupby en memoria `{h3_index: [poi, ...]}` via `_group_pois_by_cell` (O(p) donde p = total POIs).
- **Response por entrada**: un `ReachablePoisResult` por rango/perfil con `{profile, range, isochrone, pois, error}`. Errores de perfil incluidos en la lista con `pois=[]` y `error` seteado.
- **Reorganización de capas**: ports y adapters del dominio `geo_resolution` reorganizados en subfolders (`geocoding/`, `poi/`, `routing/`, `sql/`) para consistencia.

## Schemas

```
IsochroneRequest        → lat, lon, range_seconds, profile (list), property_id (opcional)
IsochroneProfileResult  → interno al OrsRoutingClient (por perfil ORS)
IsochroneEntry          → por feature GeoJSON (por rango/perfil)
ReachablePoiItem        → name, category, lat, lon, full_address, phone, website
ReachablePoisResult     → profile, range, isochrone, pois, error
```

## Open questions

- Cache-aside pendiente: key `geo:reachable:property:{property_id}` (desde property detail) vs `geo:reachable:{hash(lat,lon,range,profiles)}` (desde AVM). TTL 1h acordado, sin reverse index.

## Next steps

- Implementar cache-aside en `ResolveIsochroneUseCase` (inyectar `CachePort`).
- Conectar desde `PropertyDetailView.vue` usando el `property_id` mockeado.
