---
title: ORS routing setup + POI tag set unification
captured-from: conversation
captured-on: 2026-06-11
participants: [raul, claude]
---

## Context
Trabajo de preparación para implementar `ReachablePoiUseCase` (ADR-0006): unificar el tag set de POIs entre Overpass y el AVM, y levantar ORS con el PBF de Colombia para routing de isócronas.

## Key conclusions

### by-coordinates endpoint (catalog-service)
- `city_id` renombrado a `locality_id` en `LocationByCoordinates` schema — alias eliminado, nombre correcto.
- H3 pre-filtro agregado en `get_location_by_point`: `h3.latlng_to_cell(lat, lon, 9)` en el UC → `.where(Neighborhood.h3_cells.any(cell))` antes de `ST_Contains`. Reduce candidatos de ~1500 a 1-3.
- Cache-aside por celda H3 descartado: una celda puede caer en el borde entre dos barrios → returnaría el barrio equivocado. PostGIS es siempre el árbitro final.
- Fire-and-forget `ResolvePoiUseCase` agregado al endpoint `by-coordinates` (ya existía en `resolve-neighborhood`). Pasa `locality_id=result.locality_id`, `neighborhood_id=result.neighborhood_id`.

### POI tag set unification
- Nuevo helper `backend/catalog-service/src/app/integrations/georef/pois/category_map.py` — fuente única de verdad.
- Define 5 mapas (`_AMENITY_MAP`, `_SHOP_MAP`, `_PUBLIC_TRANSPORT_MAP`, `_LEISURE_MAP`, `_HEALTHCARE_MAP`) con las 15 categorías del AVM notebook.
- Exporta: strings para Overpass QL (`AMENITY_TAGS`, `SHOP_TAGS`, etc.) y `extract_category(tags) -> str | None`.
- `overpass.py` importa los strings — ya no tiene constantes hardcodeadas.
- `poi_provider.py` importa `extract_category` — reemplaza `_extract_category` que solo miraba 3 keys y no mapeaba a categorías estándar. `subcategories` queda `None` (concepto eliminado con la taxonomía de 15 categorías).
- OSM keys cubiertos: `amenity`, `shop`, `public_transport`, `leisure`, `healthcare` (antes solo 3).
- `platform;stop_position` omitido del tag set de `public_transport` — el `;` en el valor rompe el regex de Overpass QL.

### ORS docker setup
- Imagen: `openrouteservice/openrouteservice:nightly` (v9.10.0).
- PBF: `./data/ml/AVM/data/colombia-260510.osm.pbf` (ya existe en el repo del AVM).
- **Paths correctos para ORS nightly (v9+)** — cambiaron respecto a v7/v8:
  - OSM file: `/home/ors/files/osm_colombia.pbf` (antes era `/home/ors/ors-core/data/`)
  - Graphs: `/home/ors/graphs` (antes `/home/ors/ors-core/data/graphs`)
  - Config: `/home/ors/config` (antes `/home/ors/ors-core/data/config`)
- Paths incorrectos → ORS no encuentra el PBF → usa dataset de ejemplo bundled (Heidelberg, ~17k nodos). Señal: bounds con lon positivo (~49) en los logs.
- Config (`infra/ors/config/ors-config.yml`) y grafos (`infra/ors/graphs/`) en subfolders separados bajo `infra/ors/` para evitar que el mount de config pise el de graphs.
- Perfiles habilitados: `driving-car`, `cycling-regular`, `foot-walking`.
- `REBUILD_GRAPHS` no necesario: ORS detecta automáticamente si `graphs/` está vacío → construye; si tiene grafos → reutiliza.
- Memoria: `JAVA_OPTS: "-Xmx6g -Xms1g"` — 2GB por defecto causa OOM en cycling-regular (Colombia tiene 1.8M nodos en bici). Con 16GB de RAM y 7.7GB disponibles, 6GB de heap es seguro.
- Puerto host: `8082:8080` — evita conflicto con el container `develop` que también expone 8080.
- Swagger: `http://localhost:8082/ors/v2/swagger-ui/index.html`.
- Colombia driving-car: 1,518,187 nodos, 1,927,987 aristas, build ~670s primera vez.

### Colombia PBF — estructura
- Formato PBF: stream secuencial de nodes (lat/lon + tags), ways (lista de nodos), relations.
- osmium `SimpleHandler`: `def node(n)` se llama por cada nodo del archivo; `apply_file()` dispara el stream.
- ORS usa los **ways** con `highway=*` para construir el grafo de routing. El notebook usó los **nodes** con tags de POI. Mismo archivo, lecturas completamente distintas.
- Grafo de routing: nodo = intersección, arista = segmento de calle con peso (distancia/velocidad). Contraction Hierarchies preprocesa shortcuts entre nodos importantes para acelerar Dijkstra.
- Isocrona: snap al nodo más cercano → Dijkstra en todas direcciones hasta agotar el presupuesto de tiempo → contorno exterior de nodos alcanzables = polígono GeoJSON.

## Open questions
- Ninguna — setup completo y grafos construyendo correctamente.

## Next steps
- Esperar que terminen de construir los 3 perfiles (driving-car ✅, cycling-regular y foot-walking en progreso).
- Implementar `ReachablePoiUseCase` + integración ORS en catalog-service (ver ADR-0006).
- Init container osmium para seed de POIs de Bogotá desde el mismo PBF.
