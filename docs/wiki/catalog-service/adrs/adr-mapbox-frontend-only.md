---
title: ADR-0005 — Mapbox solo en el frontend (catalog hace reverse-only)
status: stable
last-verified: 2026-07-15
owners: [catalog-service, _shared]
related:
  - "[[catalog-service]]"
  - "[[catalog-service-architecture]]"
  - "[[adr-geo-enrichment-at-write-time]]"
  - "[[glossary]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
decision-date: 2026-05-21
decision-status: accepted
---

# ADR-0005 — Mapbox solo en el frontend (catalog hace reverse-only)

## Contexto

Al crear un listing, el usuario tipea una dirección y el sistema necesita derivar `(lat, lon)` + `barrio_ideca`. Hoy, el flujo del frontend usa Mapbox SDK para el UX (autocomplete con sugerencias, preview del punto en mapa). Pero **adicionalmente** `catalog-service` expone `/geo-resolution/resolve-neighborhood?query` que **vuelve a llamar Mapbox** del lado server para hacer forward geocoding antes del point-in-polygon.

Resultado: **duplicación**. Cada submit de listing termina haciendo 2 llamadas a Mapbox (una desde el SPA, otra desde el backend) por la misma dirección.

Además: el frontend ya tiene `(lat, lon)` validados (el usuario VE el punto en el mapa antes de submitear). Pedirle al backend que reresuelva el address agrega latencia, costo Mapbox, y un cache de forward geocode que no es estrictamente necesario.

## Decisión

**Mapbox vive en el frontend**, no en el backend. `catalog-service` hace **reverse-only**:

- El frontend (Mapbox SDK) hace [[glossary#forward-geocoding]]: address → `(lat, lon)`.
- El frontend submitea el listing con `(lat, lon)` ya resueltos.
- `properties-service` llama a `catalog-service` con esos coords para hacer [[glossary#reverse-geocoding]]: `(lat, lon) → barrio_ideca`.
- **Endpoint canónico**: `GET /v1/geo-resolution/by-coordinates?lat&lon` (que ya existe).
- **Endpoint a deprecar**: `GET /v1/geo-resolution/resolve-neighborhood?query&locality_id` (forward-then-reverse, duplica Mapbox).

Para que `/by-coordinates` sea drop-in replacement de `/resolve-neighborhood`, hacía falta un trabajo de refactor en 4 pasos (ver Migration path). **Pasos 1 y 2 ya están hechos** (2026-06-11): `/by-coordinates` dispara `BackgroundTasks.add_task(poi_uc.execute, ...)`, y `properties-service` (`CatalogClient`) ya llama `/by-coordinates` en vez de `/resolve-neighborhood`. Quedan pendientes los pasos 3 (wrapper deprecado temporal) y 4 (eliminar el código Mapbox legacy) — `/resolve-neighborhood` sigue funcionando y montado, sin tráfico conocido de consumers internos.

Este ADR documenta **el estado deseado** post-refactor; el refactor está a mitad de camino.

## Alternativas consideradas

- **Mantener forward en backend** (status quo) — duplica Mapbox por listing, latencia user-facing innecesaria, costo Mapbox doble.
- **Mover TODO al backend** (sin Mapbox SDK en frontend) — frontend pierde el UX de autocomplete + preview en mapa, sin ganar nada arquitecturalmente.
- **Backend hace forward + reverse, frontend hace TODO local** — no es viable; el SDK de Mapbox es lo que da el autocomplete UX.

## Consecuencias

- ✅ **Sin duplicación**: una sola llamada a Mapbox por listing (la del frontend).
- ✅ Menos latencia en el path crítico de crear listing.
- ✅ Menos código en el backend (remueve `integrations/georef/mapbox/`, `ResolveNeighborhoodUseCase`, schema `GeocodingResult`).
- ✅ Frontend sigue dueño del UX que ya tiene.
- ✅ `catalog-service` queda más enfocado — solo catálogo + reverse + side-effect POIs.
- ❌ Si en el futuro queremos consumir address-from-server (ej. ETL desde fuente externa que no pasa por el frontend), tocará volver a meter forward en el backend.
- ❌ El refactor requiere coordinar **3 lados**: el endpoint, los consumers (properties-service), y la limpieza del código mapbox del backend.
- ❌ Si Mapbox cambia API o sube precio, el impacto está concentrado en el frontend (menos blast radius pero misma exposición).

## Migration path

1. ✅ Agregar `BackgroundTasks` para `ResolvePoiUseCase` al endpoint `/by-coordinates` — hecho 2026-06-11.
2. ✅ Actualizar `properties-service` para llamar `/by-coordinates` en lugar de `/resolve-neighborhood` al crear listing — hecho, `CatalogClient` llama `/v1/geo-resolution/by-coordinates` ([catalog_client.py:38](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L38)); sin referencias a `resolve-neighborhood` en `properties-service` ni en el frontend.
3. ⬜ (Opcional, temporary) Hacer `/resolve-neighborhood` un wrapper deprecado que llame internamente `/by-coordinates` después del forward — para no romper consumers que no migraron.
4. ⬜ Después de N semanas sin tráfico a `/resolve-neighborhood`, borrar:
   - `ResolveNeighborhoodUseCase`, su port, su adapter, su schema.
   - `integrations/georef/mapbox/` completo.
   - `GeocodingGateway` y `GeocodingAdapter`.
   - Env `MAPBOX_API_KEY` del backend.
   - Cache `cache_key_forward_geocode` (huérfana).

## Claims

- `/geo-resolution/by-coordinates` ya existe y hace reverse-only ([api/routes/geo_resolution.py:43-49](backend/catalog-service/src/app/api/routes/geo_resolution.py#L43-L49)).
- `/geo-resolution/by-coordinates` dispara el `ResolvePoiUseCase` vía `BackgroundTasks` desde 2026-06-11 — gap del refactor cerrado ([api/routes/geo_resolution.py:56-62](backend/catalog-service/src/app/api/routes/geo_resolution.py#L56-L62)).
- `properties-service` ya no llama `/resolve-neighborhood` — su `CatalogClient` usa `/by-coordinates` ([catalog_client.py:38](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L38)).
- `/geo-resolution/resolve-neighborhood` hace forward geocoding con Mapbox + cache de 30 días en Redis ([resolve_neighborhood.py:56-87](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_neighborhood.py#L56-L87)).
- `integrations/georef/mapbox/georeferentiation.py` lee `MAPBOX_API_KEY` del entorno ([mapbox/georeferentiation.py:21](backend/catalog-service/src/app/integrations/georef/mapbox/georeferentiation.py#L21)).
- Este ADR alinea con [[adr-geo-enrichment-at-write-time]] (cross-service) — properties resuelve geo al crear listing, ahora con `lat/lon` siempre.
