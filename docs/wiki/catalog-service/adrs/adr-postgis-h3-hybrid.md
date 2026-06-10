---
title: ADR-0001 — PostGIS + h3 híbrido para spatial queries
status: stable
last-verified: 2026-06-08
owners: [catalog-service]
related:
  - "[[catalog-service-architecture]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[glossary]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md, ../../../sources/properties-service/2026-06-08-feed-cache-geo-scaling.md]
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
- ❌ **Gap actual**: el read path (`get_location_by_point`, `get_neighborhood_by_coordinates`) **no usa** `h3_cells` para pre-filtrar. El campo se popula pero no se aprovecha. Fix acordado: calcular el `h3_index` del punto en Python → `WHERE h3_index = ANY(Neighborhood.h3_cells)` (GIN index barato) → `ST_Contains` solo sobre los 1-3 candidatos. Pendiente de implementar en `SqlGeoreferentiationRepository.get_location_by_point`.
- ❌ Cold start lento por barrio: la primera vez que un punto cae en un barrio, el `h3_cells` está `NULL`. Pre-fill batch como mitigación si hace falta.
- ❌ Más deps (`geoalchemy2`, `h3`, `postgis/postgis:17-master` image) vs `postgres:17` plano.

## Claims

- `Neighborhood.geom` es `MULTIPOLYGON SRID 4326` con índice GiST `ix_neighborhood_geom` ([models/location.py:280-297](backend/catalog-service/src/app/models/location.py#L280-L297)).
- `Neighborhood.h3_cells` es `ARRAY[VARCHAR(16)]` con índice GIN `ix_neighborhood_h3_cells` ([models/location.py:287-298](backend/catalog-service/src/app/models/location.py#L287-L298)).
- `PointOfInterest.h3_index` se precomputa con `h3.latlng_to_cell(lat, lon, res=settings.H3_RESOLUTION)` y se persiste indexed ([models/location.py:375](backend/catalog-service/src/app/models/location.py#L375)).
- `settings.H3_RESOLUTION = 9` (~300 m por celda) ([core/config/settings.py:24](backend/catalog-service/src/app/core/config/settings.py#L24)).
- Los queries actuales de reverse geocoding hacen `ST_Contains` directo sin pre-filter por h3 ([sql_georeferentiation_repository.py:19-32](backend/catalog-service/src/app/services/geo_resolution/adapters/sql_georeferentiation_repository.py#L19-L32)).
- catalog-service usa la imagen `postgis/postgis:17-master`; properties-service también la usa para su DB ([docker-compose.yml:31](docker-compose.yml#L31), [docker-compose.yml:42](docker-compose.yml#L42)).
