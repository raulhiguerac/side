---
title: Integración ORS — OpenRouteService (catalog-service)
status: stable
last-verified: 2026-06-15
owners: [catalog-service]
related:
  - "[[adr-isochrone-ors-h3]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[catalog-service-architecture]]"
  - "[[adr-poi-cache-aside]]"
sources:
  - ../../../sources/catalog-service/2026-06-11-ors-setup-poi-unification.md
  - ../../../sources/catalog-service/2026-06-15-ors-isochrone-reachable-pois.md
---

## TL;DR

OpenRouteService (ORS) provee el motor de routing para isócronas. Self-hosted via Docker con el PBF de Colombia. Elegido sobre Mapbox por cobertura en red vial colombiana — ver [[adr-isochrone-ors-h3]]. Un `POST /v2/isochrones/{profile}` devuelve el polígono; catalog-service lo convierte a celdas H3 y hace lookup de POIs. Endpoint implementado: `POST /v1/geo-resolution/reachable-pois`.

## Setup docker-compose

```yaml
router:
  image: openrouteservice/openrouteservice:nightly
  ports:
    - "8082:8080"          # host:container — 8082 evita conflicto con devcontainer
  environment:
    JAVA_OPTS: "-Xmx6g -Xms1g"   # Colombia con 3 perfiles necesita >2GB
  volumes:
    - ./data/ml/AVM/data/colombia-260510.osm.pbf:/home/ors/files/osm_colombia.pbf
    - ./infra/ors/graphs:/home/ors/graphs
    - ./infra/ors/config:/home/ors/config
  networks:
    - dev-net
```

**Paths críticos para ORS nightly (v9+)** — cambiaron respecto a v7/v8:

| Recurso | Path en container |
|---|---|
| OSM file | `/home/ors/files/osm_colombia.pbf` |
| Graphs (runtime) | `/home/ors/graphs` |
| Config | `/home/ors/config/ors-config.yml` |

Paths incorrectos → ORS no encuentra el PBF → usa dataset bundled de ejemplo (Heidelberg, ~17k nodos). Señal de error: bounds con longitud positiva (~49) en los logs en vez de negativa (~-74 para Colombia).

## Configuración — `infra/ors/config/ors-config.yml`

```yaml
ors:
  engine:
    profile_default:
      build:
        source_file: /home/ors/files/osm_colombia.pbf
    profiles:
      driving-car:
        enabled: true
      cycling-regular:
        enabled: true
      foot-walking:
        enabled: true
```

Perfiles habilitados: `driving-car`, `cycling-regular`, `foot-walking` — los tres modos del ADR.

## Grafos — build y persistencia

- `infra/ors/graphs/` se monta en `/home/ors/graphs`. ORS detecta si el directorio está vacío → construye; si tiene grafos → reutiliza. No necesita `REBUILD_GRAPHS=true`.
- Primera build con Colombia: ~11 min para `driving-car` (1.5M nodos, 1.9M aristas). Cycling y walking similares.
- Grafos persistidos en el host → reinicios siguientes arrancan en segundos.
- Solo necesita `REBUILD_GRAPHS: true` si cambia el PBF (nueva versión del mapa).

## Memoria

Colombia con 3 perfiles en ORS nightly v9 requiere >2GB de heap JVM. Con `-Xmx2g` (default) crashea con OOM en cycling-regular. `-Xmx6g` es seguro con 16GB de RAM total (~7.7GB disponibles en el stack de dev).

## Colombia PBF — estadísticas del grafo construido

| Perfil | Nodos | Aristas | Build time |
|---|---|---|---|
| driving-car | 1,518,187 | 1,927,987 | ~670s |
| cycling-regular | 1,832,674 | 2,387,434 | ~similar |
| foot-walking | mayor que cycling | — | — |

Bounds correctos: `lon ∈ [-81.7, -66.8]`, `lat ∈ [-4.3, 15.8]` — Colombia + zonas limítrofes.

## API surface — isócronas

```
POST http://router:8080/ors/v2/isochrones/{profile}
```

Profiles: `driving-car`, `cycling-regular`, `foot-walking`.

Body mínimo:
```json
{
  "locations": [[-74.072, 4.710]],
  "range": [900],
  "range_type": "time"
}
```

`range` en segundos. Devuelve GeoJSON `FeatureCollection` con el polígono de isocrona.

Swagger: `http://localhost:8082/ors/v2/swagger-ui/index.html` (disponible cuando los grafos terminan de cargar).

## catalog-service integration

Stack hexagonal completo para el endpoint de POIs alcanzables:

```
OrsRoutingClient (integrations/georef/ors/routing.py)
  └─ OrsRoutingAdapter (adapters/routing/ors.py)
       └─ RoutingGateway Protocol (ports/routing/gateway.py)
            └─ ResolveIsochroneUseCase (use_cases/resolve_isochrone.py)
                 └─ POST /v1/geo-resolution/reachable-pois
```

### Endpoint público

```
POST /v1/geo-resolution/reachable-pois
```

Body (`IsochroneRequest`):

```json
{
  "lat": 4.709,
  "lon": -74.028,
  "range_seconds": [900],
  "profile": ["foot-walking", "driving-car"],
  "property_id": "uuid-opcional"
}
```

Response: `list[ReachablePoisResult]` — un elemento por perfil/rango con `{profile, range, isochrone, pois, error}`.

### Patrón de lookup H3 — 1 query para N perfiles

1. Para cada `IsochroneEntry` sin error: `h3.polygon_to_cells(LatLngPoly(exterior), res=9)` → acumula celdas en `all_cells`.
2. **Un único** `uow.pois.get_by_h3_cells(h3_cells=all_cells)` para todos los perfiles juntos.
3. Groupby en memoria: `_group_pois_by_cell` → `{h3_index: [PointOfInterest, ...]}`.
4. Por cada perfil, filtra del dict las celdas que le pertenecen.

Evita N queries (una por isócrona) — solo hay 1 hit a la DB independientemente de cuántos perfiles se pidan.

### Parallel gather

`OrsRoutingClient.get_isochrone` lanza `asyncio.gather` con una corutina por perfil. Un perfil con error (status ≠ 200) devuelve `IsochroneProfileResult(error=...)` sin bloquear los demás.

### Coordinate order

ORS usa `[lon, lat]` (GeoJSON standard). El polígono de respuesta también viene en `[lon, lat]`. La conversión a `h3.LatLngPoly` invierte: `[(lat, lng) for lng, lat in exterior]`.

### Env var

`ORS_URL` — URL base del servicio ORS. En dev local: `http://localhost:8082/ors`. Desde dentro de Docker (catalog-service container → router container en `dev-net`): `http://router:8080/ors`.

### Schemas (`services/geo_resolution/schemas/isochrone.py`)

| Schema | Uso |
|---|---|
| `IsochroneRequest` | Request body del endpoint público |
| `IsochroneProfileResult` | Interno a `OrsRoutingClient` (respuesta cruda por perfil) |
| `IsochroneEntry` | Adaptado por `OrsRoutingAdapter` (un entry por feature GeoJSON) |
| `ReachablePoiItem` | POI serializado en el response |
| `ReachablePoisResult` | Elemento del response final (por perfil/rango) |

### Cache-aside — pendiente

Ver [[adr-poi-cache-aside]] y [[open-items]]. Dos keys según el caller:
- `geo:reachable:property:{property_id}` — cuando viene desde property detail (TTL 1h).
- `geo:reachable:{hash(lat,lon,range,profiles)}` — para calls del AVM sin `property_id` (TTL 1h).
No implementado aún — `CachePort` no está inyectado en `ResolveIsochroneUseCase`.

## Claims

- ORS nightly v9 usa paths `/home/ors/files/`, `/home/ors/graphs/`, `/home/ors/config/` — distintos a v7/v8 (`/home/ors/ors-core/data/`).
- Con `-Xmx2g` (default) ORS crashea con OOM al construir cycling-regular para Colombia.
- ORS detecta grafos existentes automáticamente — no necesita `REBUILD_GRAPHS=true` en reinicios normales.
- El PBF de Colombia (`colombia-260510.osm.pbf`) está en `data/ml/AVM/data/` — mismo archivo usado por el notebook del AVM.
- `driving-car` Colombia: 1,518,187 nodos, 1,927,987 aristas, build ~670s primera vez.
- El endpoint de isócronas ORS es `POST /ors/v2/isochrones/{profile}` — `range` en segundos, `range_type: "time"`.
- Puerto host `8082` para evitar conflicto con `develop` container que expone `8080`.
- El endpoint público es `POST /v1/geo-resolution/reachable-pois` — implementado en `ResolveIsochroneUseCase` ([use_cases/resolve_isochrone.py](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_isochrone.py)).
- `OrsRoutingClient` usa `asyncio.gather` para lanzar un request por perfil en paralelo — un error en un perfil no bloquea los demás ([integrations/georef/ors/routing.py](backend/catalog-service/src/app/integrations/georef/ors/routing.py)).
- El lookup de POIs usa `get_by_h3_cells` con **todas las celdas de todos los perfiles acumuladas** — 1 query a DB sin importar cuántos perfiles se pidan ([use_cases/resolve_isochrone.py:52-54](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_isochrone.py#L52-L54)).
- ORS devuelve coordenadas en orden `[lon, lat]`; la conversión a `h3.LatLngPoly` invierte con `[(lat, lng) for lng, lat in exterior]`.
- Cache-aside de `reachable-pois` **no implementado** al 2026-06-15 — `CachePort` no inyectado en `ResolveIsochroneUseCase`.
