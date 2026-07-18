---
title: Integración Overpass (catalog-service)
status: stable
last-verified: 2026-06-23
owners: [catalog-service]
related:
  - "[[catalog-service-poi-lifecycle]]"
  - "[[catalog-service-architecture]]"
  - "[[avm-training]]"
  - "[[adr-poi-cache-aside]]"
  - "[[adr-isochrone-ors-h3]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md, ../../../sources/catalog-service/2026-06-11-ors-setup-poi-unification.md, ../../../sources/catalog-service/2026-06-23-overpass-406-and-h3-chicken-egg-fix.md]
---

## TL;DR

Overpass API (OpenStreetMap) se usa como provider de [[glossary#poi-point-of-interest]] — el backend manda una bounding box y recibe POIs categorizados. Llamado únicamente como side-effect del POI fetch (nunca on-demand, ver [[adr-poi-cache-aside]]). Tag set unificado con el AVM (5 keys OSM, 15 categorías, 100+ valores) via helper `category_map.py` — fuente única de verdad para query y clasificación. Requiere `User-Agent` descriptivo desde 2026-06-23 (la instancia pública empezó a devolver 406 sin él).

## Configuración

| Env / setting | Valor | Para qué |
|---|---|---|
| `settings.OVERPASS_TIMEOUT_SECONDS` | 30 | Timeout de cada query Overpass (cliente + dentro del QL) |
| `settings.OVERPASS_USER_AGENT` | `side-catalog-service/1.0 (contact: ...)` | Header `User-Agent` enviado a Overpass — sin esto, `overpass-api.de` responde 406 |

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

Template en [overpass.py](backend/catalog-service/src/app/integrations/georef/pois/overpass.py) — los tag strings se importan desde `category_map.py`:

```overpassql
[out:json][timeout:{timeout}];
(
  node["amenity"~"{amenity}"]{bbox};
  node["shop"~"{shop}"]{bbox};
  node["public_transport"~"{public_transport}"]{bbox};
  node["leisure"~"{leisure}"]{bbox};
  node["healthcare"~"{healthcare}"]{bbox};
  way["amenity"~"{amenity}"]{bbox};
  way["shop"~"{shop}"]{bbox};
  way["public_transport"~"{public_transport}"]{bbox};
  way["leisure"~"{leisure}"]{bbox};
  way["healthcare"~"{healthcare}"]{bbox};
);
out center;
```

- `[out:json]` — Overpass devuelve JSON.
- `[timeout:{N}]` — Overpass mata la query si excede.
- Busca **nodes** y **ways**. `out center;` da centroide de ways — el adapter lo lee como `center.lat/lon`.

## Tag set y categorías — `category_map.py`

Fuente única de verdad en [`integrations/georef/pois/category_map.py`](backend/catalog-service/src/app/integrations/georef/pois/category_map.py). Define 5 mapas `{categoría: [valores OSM]}`:

| Key OSM | Categorías | Valores aprox. |
|---|---|---|
| `amenity` | transport, food, education, health, finance, commerce, recreation, worship, adult | 33 |
| `shop` | food, commerce, fashion, home, electronics, health, auto, services, leisure, adult | 72 |
| `public_transport` | transport | 3 |
| `leisure` | recreation | 24 |
| `healthcare` | health | 15 |

**Total: 147 valores, 15 categorías estándar.**

El helper exporta:
- `AMENITY_TAGS`, `SHOP_TAGS`, `PUBLIC_TRANSPORT_TAGS`, `LEISURE_TAGS`, `HEALTHCARE_TAGS` — strings `|`-joineados para la query QL.
- `extract_category(tags: dict) -> str | None` — clasifica un elemento OSM a una de las 15 categorías. Prioridad: amenity → shop → public_transport → leisure → healthcare.

`overpass.py` importa los strings; `poi_provider.py` importa `extract_category`. `subcategories` eliminado — la taxonomía de 15 categorías lo hace innecesario.

**Nota**: `platform;stop_position` omitido del tag set de `public_transport` — el `;` en el valor rompe el regex de Overpass QL.

## Unificación con el AVM — resuelta

El tag set de [[avm-training]] (5 keys OSM, 15 categorías) y el de catalog ahora son idénticos. La columna `points_of_interest.category` queda alineada con lo que espera el modelo — el AVM puede migrar a consumir esta tabla via ETL sin inconsistencias. Ver [[adr-isochrone-ors-h3]] §7.

## Error handling

Todas las excepciones mapean al mismo error de dominio (`GeoResolutionUnavailableError(provider="overpass")`), pero desde 2026-06-23 cada categoría se captura por separado para loggear la causa real — antes caían todas en un `except Exception` genérico porque las excepciones propias de la lib `overpass` (`OverpassSyntaxError`, `MultipleRequestsError`, `ServerLoadError`, `UnknownOverpassError`) **no heredan de `requests.exceptions`**:

| Excepción de la lib | Causa típica | Log |
|---|---|---|
| `requests.exceptions.ConnectionError`, `Timeout` | Red/DNS, timeout de conexión | `overpass_unreachable` |
| `requests.exceptions.HTTPError` | Error HTTP de `requests` | `overpass_http_error` |
| `overpass.errors.OverpassSyntaxError` | Overpass respondió 400 | `overpass_syntax_error` |
| `overpass.errors.MultipleRequestsError` | Overpass respondió 429 (rate limit) | `overpass_rate_limited` |
| `overpass.errors.ServerLoadError` | Overpass respondió 504 (server sobrecargado) | `overpass_server_overloaded` |
| `overpass.errors.UnknownOverpassError` | Cualquier otro status code, incluye el 406 antes del fix de User-Agent | `overpass_unknown_error` |
| `Exception` (catch-all) | Lo no anticipado | `overpass_unexpected_error` |

**Nota sobre el logging**: `setup_logging()` ([core/logging/logger.py](backend/catalog-service/src/app/core/logging/logger.py)) usa un formato fijo con solo `%(message)s` — cualquier `extra={...}` pasado a `logger.error`/`warning` se **descarta siempre**, en todo el servicio (no solo aquí). Por eso estos logs interpolan el motivo directo en el string del mensaje en vez de pasarlo por `extra`.

El catch-all sigue ahí para lo verdaderamente inesperado. Aceptable porque el llamador es un background task que no propaga al user.

## Caching y dedup (recap)

El cache + dedup viven en el UC `ResolvePoiUseCase`, no en este cliente. Tres capas (Redis short-circuit, Redis `SET NX` lock, DB `FetchZone` freshness). Detalle completo en [[catalog-service-poi-lifecycle]].

## Claims

- `PoiClient.get_pois_by_bbox` es el único método del cliente ([overpass.py](backend/catalog-service/src/app/integrations/georef/pois/overpass.py)).
- Timeout configurado vía `settings.OVERPASS_TIMEOUT_SECONDS` (30s default).
- La query QL cubre 5 keys OSM con 147 valores en total, joineados con `|` como regex.
- Los tag strings y `extract_category` se importan desde `category_map.py` — `overpass.py` no tiene constantes hardcodeadas de tags.
- `extract_category(tags)` aplica prioridad amenity → shop → public_transport → leisure → healthcare y devuelve una de 15 categorías estándar o `None` ([category_map.py](backend/catalog-service/src/app/integrations/georef/pois/category_map.py)).
- `subcategories` en `PointOfInterest` se persiste como `None` — eliminado con la taxonomía de 15 categorías.
- La query usa `out center;` para que Overpass devuelva centroide de ways/areas.
- 7 categorías de error capturadas (incl. catch-all), todas mapean a `GeoResolutionUnavailableError(provider="overpass")`, cada una con su propio log para no perder la causa ([overpass.py](backend/catalog-service/src/app/integrations/georef/pois/overpass.py)).
- `PoiClient` pasa `headers={"User-Agent": settings.OVERPASS_USER_AGENT, "Accept-Charset": "utf-8;q=0.7,*;q=0.7"}` a `overpass.API(...)` — sin esto, `overpass-api.de` responde 406 a cualquier request (confirmado con curl, no es específico de la lib Python). Fix 2026-06-23.
- El tag set de catalog y el del training del AVM están unificados al 2026-06-11.
