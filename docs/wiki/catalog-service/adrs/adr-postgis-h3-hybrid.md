---
title: ADR-0001 — PostGIS + h3 híbrido para spatial queries
status: stable
last-verified: 2026-07-18
owners: [catalog-service]
related:
  - "[[catalog-service-architecture]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[glossary]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md, ../../../sources/properties-service/2026-06-08-feed-cache-geo-scaling.md, ../../../sources/catalog-service/2026-06-23-overpass-406-and-h3-chicken-egg-fix.md, ../../../sources/catalog-service/2026-07-18-h3-precompute-and-bulk-resolve.md]
decision-date: 2026-05-21
decision-status: accepted
---

# ADR-0001 — PostGIS + h3 híbrido para spatial queries

## Contexto

`catalog-service` necesita responder dos clases de queries espaciales:
1. **Reverse geocoding**: dado `(lat, lon)`, encontrar el barrio que lo contiene (`point-in-polygon` contra ~1.500 polígonos IDECA por locality grande).
2. **POI fetching**: dada una celda, fetchear POIs vecinos desde Overpass y persistirlos.

`ST_Contains(geom, point)` directo escala mal: PostGIS evalúa el polígono completo de cada candidato, y el GiST index acelera pero no es gratis. Para Bogotá (~1.500 barrios) la latencia P99 puede degradarse rápido.

## Decisión

Diseño híbrido:

- **PostGIS** ([[glossary#postgis]]) como ground truth: `Neighborhood.geom MULTIPOLYGON SRID 4326` con índice GiST, `PointOfInterest.geom POINT` con índice GiST.
- **h3** ([[glossary#h3]]) como **índice de aceleración barato**: `Neighborhood.h3_cells` array de strings indexed via GIN, `PointOfInterest.h3_index` (precomputed res=9, ~300 m), `FetchZone.h3_index` (res=9, unique).
- El read path **debería** filtrar primero por `h3_cells @> ARRAY[$query_h3]` (reduce a 1-3 candidatos) y luego `ST_Contains` exacto sobre esos.

## Alternativas consideradas

- **PostGIS puro** sin h3 — más simple pero escala peor; no aprovecha que h3 ya se usa en `analytics-service` training.
- **h3 puro** sin geometría exacta — pierde precisión: una celda h3 puede estar a caballo entre dos barrios; sin `ST_Contains` no hay desambiguación.
- **Tile server** dedicado (Tegola, Martin) — overkill para el read pattern actual; agrega un nuevo deploy.
- **Spatial index custom** (Quadtree in-memory) — más control pero más cosas para mantener.

## Consecuencias

- ✅ Ground truth + aceleración separados — cada uno optimiza lo suyo.
- ✅ Mismo sistema h3 que [[avm-training]] — consistencia conceptual cross-servicio.
- ✅ `h3_cells` se llena gradualmente con el tráfico real (lazy-fill, ver [[catalog-service-poi-lifecycle]]) — los barrios populares se aceleran solos.
- ✅ **Agregado 2026-07-18 — precompute en enrich time**: además del lazy-fill, `BulkEnrichNeighborhoodGeometriesUseCase` y `EnrichNeighborhoodGeometryUseCase` ahora calculan `h3_cells` completo (cobertura del polígono entero, no solo la celda pisada por tráfico real) al mismo tiempo que setean `geom`, vía `h3_cells_for_geojson(geometry, resolution=settings.H3_RESOLUTION)`. Reduce el cold start para barrios que pasan por estos flujos — pero **no lo elimina**: `CreateNeighborhoodUseCase`/`UpdateNeighborhoodUseCase` nunca tocan `geom`/`h3_cells`, y el polyfill de h3 decide membership por centroide de celda, así que un punto cerca del borde puede caer en una celda no incluida en el precompute aunque `ST_Contains` sea true. El fallback sin pre-filtro sigue siendo necesario por ambas razones, no es vestigial.
- ✅ **Agregado 2026-07-18 — dedup en el append**: `update_neighborhood_h3_cells` usaba `array_append` incondicional — cada ciclo de stale→refetch en `ResolvePoiUseCase` reinsertaba el mismo `h3_index`, duplicando entradas indefinidamente. Fix confinado al SQL (`CASE WHEN h3_cells.any(h3_index) THEN h3_cells ELSE array_append(...)`), sin tocar la lógica de `resolve_poi.py`.
- ✅ **Cerrado 2026-06-23 para `get_location_by_point`**: el read path de `/geo-resolution/by-coordinates` ahora hace `WHERE h3_cells.any($h3_index) AND ST_Contains(geom, point)` primero (acota a 1-3 candidatos vecinos cuando la celda ya está poblada); si no hay candidatos (celda fría, nunca poblada), cae a un `ST_Contains` completo sobre todos los barrios con `geom`. Importante: el pre-filtro **nunca decide solo** — siempre se valida con `ST_Contains`, porque una celda h3 puede solapar 2 barrios cerca de un borde y el pre-filtro solo podía devolver el vecino equivocado.
- ❌ **Sigue abierto para `get_neighborhood_by_coordinates`** (resolve-neighborhood por dirección, vía Mapbox forward geocode): sigue haciendo `ST_Contains` directo sin pre-filtro por `h3_cells`. No se tocó en este fix.
- ❌ Cold start lento por barrio: la primera vez que un punto cae en un barrio, el `h3_cells` está `NULL` y cae al `ST_Contains` completo (más caro, pero correcto). El `background_tasks.add_task(poi_uc.execute, ...)` en `/by-coordinates` puebla la celda para la próxima request. Pre-fill batch sigue siendo mitigación posible si hace falta acelerar el primer hit.
- ❌ Más deps (`geoalchemy2`, `h3`, `postgis/postgis:17-master` image) vs `postgres:17` plano.

## Claims

- `Neighborhood.geom` es `MULTIPOLYGON SRID 4326` con índice GiST `ix_neighborhood_geom` ([models/location.py:280-297](backend/catalog-service/src/app/models/location.py#L280-L297)).
- `Neighborhood.h3_cells` es `ARRAY[VARCHAR(16)]` con índice GIN `ix_neighborhood_h3_cells` ([models/location.py:287-298](backend/catalog-service/src/app/models/location.py#L287-L298)).
- `PointOfInterest.h3_index` se precomputa con `h3.latlng_to_cell(lat, lon, res=settings.H3_RESOLUTION)` y se persiste indexed ([models/location.py:375](backend/catalog-service/src/app/models/location.py#L375)).
- `settings.H3_RESOLUTION = 9` (~300 m por celda) ([core/config/settings.py:24](backend/catalog-service/src/app/core/config/settings.py#L24)).
- `get_neighborhood_by_coordinates` (resolve-neighborhood por dirección) hace `ST_Contains` directo sin pre-filtro por h3 ([sql_georeferentiation_repository.py:19-32](backend/catalog-service/src/app/services/geo_resolution/adapters/sql_georeferentiation_repository.py#L19-L32)).
- `get_location_by_point` (by-coordinates) sí pre-filtra: `h3_cells.any(cell) AND ST_Contains(...)` primero, con fallback a `ST_Contains` completo si no hay candidatos por h3 ([sql_georeferentiation_repository.py:58-84](backend/catalog-service/src/app/services/geo_resolution/adapters/sql_georeferentiation_repository.py#L58-L84)).
- `get_location_by_points` (batch, 2026-07-18) aplica el mismo patrón de dos pasadas (prefiltro h3 vía `unnest`+`LATERAL JOIN`, luego fallback sin prefiltro solo para los misses) en vez de N llamadas a `get_location_by_point` ([sql_georeferentiation_repository.py](backend/catalog-service/src/app/services/geo_resolution/adapters/sql/georeferentiation_repository.py)).
- `BulkEnrichNeighborhoodGeometriesUseCase` y `EnrichNeighborhoodGeometryUseCase` precomputan `h3_cells` con `h3_cells_for_geojson()` al setear `geom`, además del lazy-fill vía `ResolvePoiUseCase` ([shared/helpers/geometry.py](backend/catalog-service/src/app/services/shared/helpers/geometry.py)).
- `update_neighborhood_h3_cells` evita duplicados: `h3_cells = CASE WHEN h3_cells.any(h3_index) THEN h3_cells ELSE array_append(h3_cells, h3_index) END` ([sql/georeferentiation_repository.py:39-48](backend/catalog-service/src/app/services/geo_resolution/adapters/sql/georeferentiation_repository.py#L39-L48)).
- catalog-service usa la imagen `postgis/postgis:17-master`; properties-service también la usa para su DB ([docker-compose.yml:31](docker-compose.yml#L31), [docker-compose.yml:42](docker-compose.yml#L42)).
