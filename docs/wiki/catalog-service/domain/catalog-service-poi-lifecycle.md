---
title: Lifecycle del POI (catalog-service)
status: draft
last-verified: 2026-05-21
owners: [catalog-service]
related:
  - "[[catalog-service]]"
  - "[[catalog-service-architecture]]"
  - "[[catalog-service-overpass]]"
  - "[[avm-training]]"
  - "[[adr-poi-cache-aside]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
---

## TL;DR

Los POIs se pueblan **side-effect only** — nunca on-demand de un endpoint, solo como background task disparada por un geo-resolution exitoso. 3 capas de dedup para evitar fetches redundantes a Overpass: Redis cache short-circuit → Redis `SET NX` lock distribuido → DB `FetchZone` freshness check. Cuando fetchea, también appendea el `h3_index` al array `h3_cells` del barrio (mecánica lazy-fill). El read path actual **no usa** `h3_cells` para pre-filtrar — gap pendiente.

## Trigger

`ResolvePoiUseCase.execute(lat, lon, locality_id, neighborhood_id)` se dispara como `BackgroundTasks` desde [`/geo-resolution/resolve-neighborhood`](backend/catalog-service/src/app/api/routes/geo_resolution.py#L32-L38).

> Hoy `/geo-resolution/by-coordinates` **NO** dispara el background task. Es uno de los gaps del refactor pendiente — ver [[catalog-service]] roadmap.

Es **fire-and-forget**: la respuesta al user va antes; un error en el POI fetch no propaga al usuario.

## Las 3 capas de dedup

```
                 ┌─────────────────────────────────────────────────────┐
                 │  ResolvePoiUseCase.execute(lat, lon, lid, nid)     │
                 └────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
                       1. Compute h3_index = h3.latlng_to_cell(lat, lon, res=9)
                                      │
                                      ▼
              ┌───────────────────────┴─────────────────────────────┐
              │ 2. Redis cache short-circuit                       │
              │    cache.get(cache_key_fetch_zone(h3_index))       │
              └───────────────────────┬─────────────────────────────┘
                          hit?  ──── yes ───► EXIT
                                      │ no
                                      ▼
              ┌───────────────────────┴─────────────────────────────┐
              │ 3. Redis distributed lock (SET NX, TTL 30s)         │
              │    cache.set_nx(lock_key_fetch_zone(h3_index))      │
              └───────────────────────┬─────────────────────────────┘
                       acquired? ─── no ───► EXIT (alguien fetcheando)
                                      │ yes
                                      ▼
              ┌───────────────────────┴─────────────────────────────┐
              │ 4. DB FetchZone freshness check                    │
              │    uow.fetch_zones.get_by_h3_index(h3_index)       │
              └───────────────────────┬─────────────────────────────┘
                                      │
        ┌──────────────────┬──────────┴──────────┬─────────────────┐
        │                  │                     │                 │
   fresh < 30d        is_stale=True          old + not stale      no fetch_zone
        │                  │                     │                 │
        ▼                  ▼                     ▼                 ▼
   set cache TTL    refetch+persist         mark stale,        fetch+persist
   con remaining    + commit                commit (próxima    + commit
        │                  │                 ejecución         │
        ▼                  ▼                 refetcha)         ▼
       EXIT          set cache TTL             ▼              set cache TTL
                                              EXIT
```

Todo el bloque va dentro de un `try/finally` que **siempre** libera el lock al salir: `cache.delete(lock_key)`.

## Cache keys involucradas

Definidas en [`geo_resolution/helpers/cache_keys.py`](backend/catalog-service/src/app/services/geo_resolution/helpers/cache_keys.py):

| Función | Key | Para qué |
|---|---|---|
| `cache_key_fetch_zone(h3_index)` | `geo:fetch_zone:<h3>` | Short-circuit — si existe, la zona se considera fresca |
| `lock_key_fetch_zone(h3_index)` | `geo:fetch_zone:lock:<h3>` | Lock distribuido para evitar fetches concurrentes a la misma zona |
| `cache_key_forward_geocode(query, locality_id)` | `geo:fwd:<sha256[:16]>` | (no usada en este UC) — cache del result de Mapbox en `ResolveNeighborhoodUseCase` |

TTLs:
- Cache `fetch_zone`: hasta `STALE_THRESHOLD_DAYS * 86400` (default 30 días) desde el `fetched_at`.
- Lock `fetch_zone:lock`: `POI_LOCK_TTL_SECONDS` (default 30s). Auto-expira si el fetcher crashea.

## El fetch_and_persist

[`_fetch_and_persist`](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_poi.py#L117-L160) hace 4 cosas en orden:

1. **Bbox de la celda H3**: `h3.cell_to_boundary(h3_index)` → `[min_lat, min_lon, max_lat, max_lon]`.
2. **Llamada a Overpass**: `poi_provider.get_pois_by_bbox(bbox, locality_id, neighborhood_id, h3_index)` → `list[PointOfInterest]` ya armados (ver más abajo).
3. **Persistir POIs**: `uow.pois.add_many(pois)`.
4. **Registrar FetchZone**: `uow.fetch_zones.add_or_update(FetchZone(locality_id, h3_index, poi_count, fetched_at=now))`.
5. **Append a `h3_cells` del barrio**: `uow.georef.update_neighborhood_h3_cells(neighborhood_id, h3_index)` — esto es la lazy-fill mechanism literal, vía `array_append` de PostgreSQL.
6. `commit()` único al final.
7. Set cache `fetch_zone` con TTL = 30 días.

## Adapter de Overpass — mapping a `PointOfInterest`

[`PoiProviderAdapter.get_pois_by_bbox`](backend/catalog-service/src/app/services/geo_resolution/adapters/poi_provider.py) toma el `geojson` que devuelve `PoiClient` (la lib Overpass) y mapea cada element del response:

- Filtra elements sin `tags.name` (POI anónimo no sirve).
- Extrae coords: si `type=node` → `lat/lon` directos; si `type=way` (o area) → `center.lat/lon` (Overpass devuelve eso por la directiva `out center`).
- **Category**: primer tag presente entre `[amenity, leisure, shop]`. **Subcategories**: los demás tags en esa lista.
- **`external_id`**: `f"{type}/{id}"` (ej: `node/123456`, `way/789012`) — único entre todos los providers porque el unique constraint es `(external_id, source)`.
- **`raw_response`**: el element completo en JSON, para poder extraer fields adicionales a futuro sin re-fetch.
- **`full_address`**: construido de `addr:street + addr:housenumber` si existen.
- Otros: `phone`, `website` de tags OSM.
- **`source`**: `PoiSource.osm` hardcodeado.
- **`h3_index`**: el de la zona (precomputed, no se re-calcula por POI).

## La lazy-fill de `h3_cells` — gap actual

`update_neighborhood_h3_cells` ([sql_georeferentiation_repository.py:34-41](backend/catalog-service/src/app/services/geo_resolution/adapters/sql_georeferentiation_repository.py#L34-L41)) ejecuta:

```sql
UPDATE neighborhoods
SET h3_cells = array_append(h3_cells, $h3_index)
WHERE id = $neighborhood_id
```

Cada zona fetcheada agrega **una celda** al array. Con tráfico real, los barrios populares van llenando su array de h3_cells; los olvidados quedan vacíos.

**El gap**: el read path actual (`get_location_by_point` y `get_neighborhood_by_coordinates`) hace `ST_Contains(geom, point)` directo sin usar `h3_cells` para pre-filtrar. O sea: hoy `h3_cells` se popula pero **no se aprovecha** para acelerar las queries. La optimización descrita en [[catalog-service]] (3-1500 candidatos PostGIS → 1-3 con H3 pre-filtro) está **diseñada pero no implementada en el read path**.

Para activarla, los reads tendrían que cambiar a algo como:

```sql
SELECT * FROM neighborhoods
WHERE locality_id = $locality_id
  AND h3_cells @> ARRAY[$query_h3]::varchar[]
  AND ST_Contains(geom, $point);
```

Pendiente medir si hace falta (la latencia actual con `ST_Contains` directo puede ser aceptable mientras los barrios sean pocos por locality).

## Refresh batch — diseñado, no implementado

`FetchZone.is_stale` se setea automáticamente cuando una zona vencida es chequeada por el UC (caso "old + not stale" del diagrama). Pero **nada lo dispara cíclicamente**.

El diseño esperado: un worker cron que itere `SELECT * FROM fetch_zones WHERE is_stale=True` y dispare `resolve_poi` para cada una. **Sin código al 2026-05-21.** Ver Open items en [[catalog-service]].

## Failure modes

- **Overpass down**: `GeoResolutionUnavailableError` propaga dentro del UC → `rollback()` → lock liberado en `finally` → la respuesta al user ya se envió (era background task), así que el user no ve nada. Próxima request a la misma zona vuelve a intentar.
- **Redis down**: el short-circuit cache falla → se intenta el lock (`set_nx`) → si falla también, el UC sigue contra DB. El **lock no protege** si Redis está down (riesgo: fetches concurrentes a la misma zona desde múltiples instancias del servicio). Aceptable a escala actual.
- **DB write parcial**: el `try/except` general hace `rollback()`; el lock se libera en `finally`. La zona queda sin `FetchZone` y será reintentada en la próxima request.

## Boundaries

- **Nunca expuesto vía HTTP** — solo invocado como background task.
- **No consume tokens** — el `principal` no es relevante para POI fetching (los datos vienen del provider, no del usuario).
- **No filtra POIs por categoría** — guarda todo lo que Overpass devuelve con `name`. El consumidor (el modelo ML futuro) decide qué tags usar.

## Open items

- **Activar H3 pre-filter en el read path** — el campo `h3_cells` se popula pero no se usa para acelerar `ST_Contains`. Medir P99 con dataset real antes de implementar.
- **Refresh batch para zonas stale** — hoy una zona vencida solo se marca `is_stale=True` pero nadie la refetcha hasta que alguien pase por ahí.
- **Tag set Overpass diverge del training del AVM** — ver [[catalog-service]] Open items.
- **Add `BackgroundTasks` al endpoint `/by-coordinates`** — parte del refactor de `/geo-resolution`.

## Claims

- `ResolvePoiUseCase` es invocado únicamente como `BackgroundTasks.add_task(...)` desde el endpoint `/geo-resolution/resolve-neighborhood`; nunca on-demand ([api/routes/geo_resolution.py:32-38](backend/catalog-service/src/app/api/routes/geo_resolution.py#L32-L38)).
- 3 capas de dedup: cache short-circuit (`cache_key_fetch_zone`) → lock distribuido (`set_nx`, TTL `POI_LOCK_TTL_SECONDS`=30s) → DB `FetchZone` freshness ([resolve_poi.py:62-103](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_poi.py#L62-L103)).
- El lock SIEMPRE se libera en `finally`, sin importar el flow ([resolve_poi.py:114-115](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_poi.py#L114-L115)).
- El append de `h3_cells` es `UPDATE ... SET h3_cells = array_append(h3_cells, $h3)` ejecutado después de persistir los POIs ([sql_georeferentiation_repository.py:34-41](backend/catalog-service/src/app/services/geo_resolution/adapters/sql_georeferentiation_repository.py#L34-L41)).
- `get_location_by_point` y `get_neighborhood_by_coordinates` usan `ST_Contains(geom, point)` directamente — sin pre-filter por `h3_cells` al 2026-05-21 ([sql_georeferentiation_repository.py:19-32](backend/catalog-service/src/app/services/geo_resolution/adapters/sql_georeferentiation_repository.py#L19-L32), [sql_georeferentiation_repository.py:58-67](backend/catalog-service/src/app/services/geo_resolution/adapters/sql_georeferentiation_repository.py#L58-L67)).
- `PoiProviderAdapter` extrae `category` del primer tag presente entre `amenity/leisure/shop` y mete los demás como `subcategories` ([poi_provider.py:15-22](backend/catalog-service/src/app/services/geo_resolution/adapters/poi_provider.py#L15-L22)).
- POIs sin `name` se descartan en el mapping ([poi_provider.py:53-54](backend/catalog-service/src/app/services/geo_resolution/adapters/poi_provider.py#L53-L54)).
- `external_id` se construye como `f"{type}/{id}"` (`node/123`, `way/456`) y junto con `source` forma el unique constraint `uq_poi_external_id_source` ([poi_provider.py:68](backend/catalog-service/src/app/services/geo_resolution/adapters/poi_provider.py#L68), [models/location.py:392](backend/catalog-service/src/app/models/location.py#L392)).
- `raw_response` persiste el element completo del Overpass response como JSON, para extraer fields adicionales sin re-fetch ([poi_provider.py:75](backend/catalog-service/src/app/services/geo_resolution/adapters/poi_provider.py#L75)).
- Refresh batch de zonas stale: **diseñado pero no implementado** al 2026-05-21.
