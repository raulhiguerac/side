---
title: Integración ORS — OpenRouteService (catalog-service)
status: stable
last-verified: 2026-06-11
owners: [catalog-service]
related:
  - "[[adr-isochrone-ors-h3]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[catalog-service-architecture]]"
sources: [../../../sources/catalog-service/2026-06-11-ors-setup-poi-unification.md]
---

## TL;DR

OpenRouteService (ORS) provee el motor de routing para isócronas (`ReachablePoiUseCase`). Self-hosted via Docker con el PBF de Colombia. Elegido sobre Mapbox por cobertura en red vial colombiana — ver [[adr-isochrone-ors-h3]]. Un `POST /v2/isochrones/{profile}` devuelve el polígono; catalog-service lo convierte a celdas H3 y hace lookup de POIs.

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

## Claims

- ORS nightly v9 usa paths `/home/ors/files/`, `/home/ors/graphs/`, `/home/ors/config/` — distintos a v7/v8 (`/home/ors/ors-core/data/`).
- Con `-Xmx2g` (default) ORS crashea con OOM al construir cycling-regular para Colombia.
- ORS detecta grafos existentes automáticamente — no necesita `REBUILD_GRAPHS=true` en reinicios normales.
- El PBF de Colombia (`colombia-260510.osm.pbf`) está en `data/ml/AVM/data/` — mismo archivo usado por el notebook del AVM.
- `driving-car` Colombia: 1,518,187 nodos, 1,927,987 aristas, build ~670s primera vez.
- El endpoint de isócronas es `POST /ors/v2/isochrones/{profile}` — `range` en segundos, `range_type: "time"`.
- Puerto host `8082` para evitar conflicto con `develop` container que expone `8080`.
