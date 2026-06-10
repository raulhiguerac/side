---
title: Integración Overpass (catalog-service)
status: draft
last-verified: 2026-05-21
owners: [catalog-service]
related:
  - "[[catalog-service-poi-lifecycle]]"
  - "[[catalog-service-architecture]]"
  - "[[avm-training]]"
  - "[[adr-poi-cache-aside]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
---

## TL;DR

Overpass API (OpenStreetMap) se usa como provider de [[glossary#poi-point-of-interest]] — el backend manda una bounding box y recibe POIs categorizados. Llamado únicamente como side-effect del POI fetch (nunca on-demand, ver [[adr-poi-cache-aside]]). Tag set hardcodeado y reducido (~15 tags) — diverge significativamente del tag set del training del AVM, conciliación pendiente.

## Configuración

| Env / setting | Valor | Para qué |
|---|---|---|
| `settings.OVERPASS_TIMEOUT_SECONDS` | 30 | Timeout de cada query Overpass (cliente + dentro del QL) |

No hay credenciales — Overpass es gratuita pero **rate-limited** (sin límites publicados estrictos, regla práctica: < 1 query/s). Por eso el dedup distribuido es crítico ([[catalog-service-poi-lifecycle]]).

## API surface

### Cliente bajo nivel: `PoiClient` ([integrations/georef/pois/overpass.py](backend/catalog-service/src/app/integrations/georef/pois/overpass.py))

Wrappea la librería `overpass` (pip `overpass>=0.7.2`). Un solo método público:

```python
async def get_pois_by_bbox(*, bbox: list[float]) -> dict:
```

- `bbox` es `[min_lat, min_lon, max_lat, max_lon]`.
- Construye una query Overpass QL desde un template (ver abajo).
- Ejecuta `self.api.get(query, build=False)` envuelto en `asyncio.to_thread`.
- Devuelve el dict con `elements` (lista de nodes/ways/areas).

### Port + adapter: `PoiProviderGateway` + `PoiProviderAdapter`

[`PoiProviderAdapter`](backend/catalog-service/src/app/services/geo_resolution/adapters/poi_provider.py) implementa el port y transforma el response Overpass en una lista de `PointOfInterest` listas para persistir. Mapping detallado en [[catalog-service-poi-lifecycle]] sección "Adapter de Overpass — mapping a `PointOfInterest`".

## La query QL

Template hardcodeado en [overpass.py:29-40](backend/catalog-service/src/app/integrations/georef/pois/overpass.py#L29-L40):

```overpassql
[out:json][timeout:{timeout}];
(
  node["amenity"~"{amenity}"]{bbox};
  node["leisure"~"{leisure}"]{bbox};
  node["shop"~"{shop}"]{bbox};
  way["amenity"~"{amenity}"]{bbox};
  way["leisure"~"{leisure}"]{bbox};
  way["shop"~"{shop}"]{bbox};
);
out center;
```

Notas técnicas:
- `[out:json]` — Overpass devuelve JSON (más fácil que XML).
- `[timeout:{N}]` — Overpass mata la query si excede.
- Busca tanto **nodes** (puntos) como **ways** (líneas/polígonos: edificios, parques).
- `out center;` — para ways y areas, Overpass calcula el centroide y lo agrega como `center: {lat, lon}` en el response. Eso simplifica el adapter (no hay que tratar geometry).

## Tag set actual

Tres listas hardcodeadas, joineadas con `|` como regex alternativos en la query:

**AMENITY_TAGS** (~13):
`restaurant, cafe, fast_food, school, kindergarten, university, hospital, clinic, pharmacy, bank, atm, bus_station, fuel`

**LEISURE_TAGS** (~4):
`park, playground, fitness_centre, sports_centre`

**SHOP_TAGS** (~3):
`supermarket, mall, convenience`

Total: **~20 tags efectivos** (subset cuidado).

## Divergencia con el training del AVM

[[avm-training]] usa un tag set **mucho más amplio** definido en `data/ml/AVM/training/feature_store/constants.py` — ~150 tags categorizados en 7 grupos:

| Grupo en analytics | En catalog hoy |
|---|---|
| `transport` (bus_station, taxi, bicycle_parking, parking, bicycle_rental) | parcial (solo `bus_station`, `fuel` bajo amenity) |
| `food` (restaurant, cafe, fast_food, bar, pub, food_court, juice_bar, ice_cream) | parcial (3 de 8) |
| `education` (school, college, university, kindergarten, language_school, music_school, driving_school) | parcial (3 de 7) |
| `health` (hospital, clinic, pharmacy, doctors, dentist, veterinary) | parcial (3 de 6) |
| `finance` (bank, atm, bureau_de_change, money_transfer) | parcial (2 de 4) |
| `commerce`, `recreation`, `worship` | ausentes |
| `shop` (supermarket, convenience, mall, +20 más) | parcial (3 de 23) |
| `leisure` (park, garden, playground, dog_park, sports_*, swimming_pool, etc.) | parcial (4 de ~20) |
| `public_transport`, `healthcare` (tags top-level distintos) | ausentes — el QUERY_TEMPLATE no los chequea |

**Consecuencia**: el side-effect actual de `ResolvePoiUseCase` puebla un subset insuficiente para que el modelo AVM se entrene contra esta tabla. Por eso training sigue usando un CSV manual de OSM ([[avm-training]] sección "POI source").

**Plan de conciliación** (pendiente):
- Decidir quién es source-of-truth del tag set: ¿analytics define y catalog adopta? ¿Mantenemos dos vistas (catalog para frontend UX, analytics para ML)?
- Si convergen: extraer el tag set a un módulo compartido (ej. `_shared/poi_taxonomy.py`) e importar desde ambos lados.
- Si divergen: documentar explícitamente que la tabla `points_of_interest` de catalog **no** es el feature store del modelo.

## Error handling

Tres categorías capturadas en el cliente, todas mapean al mismo error de dominio:

| Excepción de la lib | Error de dominio |
|---|---|
| `requests.exceptions.ConnectionError`, `Timeout` | `GeoResolutionUnavailableError(provider="overpass")` |
| `requests.exceptions.HTTPError` | `GeoResolutionUnavailableError(provider="overpass")` |
| `Exception` (catch-all) | `GeoResolutionUnavailableError(provider="overpass")` |

El catch-all es liberal — cualquier error inesperado del SDK termina como "Overpass no disponible". Aceptable porque el llamador es un background task que no propaga al user.

## Caching y dedup (recap)

El cache + dedup viven en el UC `ResolvePoiUseCase`, no en este cliente. Tres capas (Redis short-circuit, Redis `SET NX` lock, DB `FetchZone` freshness). Detalle completo en [[catalog-service-poi-lifecycle]].

## Claims

- `PoiClient.get_pois_by_bbox` es el único método del cliente ([overpass.py:48](backend/catalog-service/src/app/integrations/georef/pois/overpass.py#L48)).
- Timeout configurado vía `settings.OVERPASS_TIMEOUT_SECONDS` (30s default) ([overpass.py:46](backend/catalog-service/src/app/integrations/georef/pois/overpass.py#L46), [settings.py:25](backend/catalog-service/src/app/core/config/settings.py#L25)).
- La query QL es un template con 3 listas de tags (~20 totales) joineadas con `|` ([overpass.py:12-40](backend/catalog-service/src/app/integrations/georef/pois/overpass.py#L12-L40)).
- La query usa `out center;` para que Overpass devuelva centroide de ways/areas — el adapter lo lee como `center.lat/lon`.
- 3 categorías de error capturadas, todas mapean a `GeoResolutionUnavailableError(provider="overpass")` ([overpass.py:64-90](backend/catalog-service/src/app/integrations/georef/pois/overpass.py#L64-L90)).
- Tag set hoy: ~20 tags vs ~150 en [[avm-training]] (`data/ml/AVM/training/feature_store/constants.py`).
- El catch-all general (`except Exception`) significa que cualquier error inesperado del SDK queda registrado como provider down.
- Llamado únicamente desde `PoiProviderAdapter`, que a su vez solo es invocado por `ResolvePoiUseCase` (fire-and-forget background task).
