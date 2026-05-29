---
title: Dominio search — properties-service
status: draft
last-verified: 2026-05-28
owners: [properties-service]
related: [[properties-service]], [[properties-service-architecture]], [[adr-feed-ads-organic-injection]], [[adr-h3-dual-resolution-map]]
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

El dominio público de **descubrimiento**: el feed paginado (mezcla orgánico + promociones) y el feed-mapa por viewport. Sin auth. El feed pagina por cursor y degrada las preferencias por fases; el mapa traduce un bounding box a celdas H3 con cache-aside por celda.

## Use cases

| UC | Archivo | Qué hace |
|---|---|---|
| `GetFeedUseCase` | `use_cases/get_feed.py` | Feed paginado: ads intercalados en orgánico cada N posiciones. |
| `GetFeedMapUseCase` | `use_cases/get_feed_map.py` | Properties dentro de un bbox, resueltas vía celdas H3 + cache-aside. |

Helpers: `helpers/feed/organic.py` (orgánico con fallback de fases) y `helpers/feed/ads.py` (promociones con cache por ciudad/global).

## Feed (`GetFeed`)

Composición de cada página (`FEED_PAGE_SIZE` = 20 por default):

1. `get_ads(preferences)` — trae promociones (cacheadas).
2. `ads_per_page = min(len(ads), page_size // FEED_AD_INTERVAL)`; `organic_count = page_size - ads_per_page`.
3. `get_organic(...)` — trae los orgánicos faltantes.
4. `_inject_ads` — intercala un ad cada `FEED_AD_INTERVAL` (default 5) posiciones orgánicas; el ad de arranque rota según la posición del cursor.

Corte duro: si `cursor.position >= FEED_MAX_RESULTS` (300) → devuelve `[]`.

### Orgánico con fallback de fases

`get_organic` ejecuta hasta tres "fases" de relajación de preferencias y devuelve la primera no vacía ([organic.py:44-60](backend/properties-service/src/app/services/search/helpers/feed/organic.py#L44-L60)):

1. barrio + ciudad + tipo de propiedad
2. ciudad + tipo (sin barrio)
3. sin filtros de preferencia (solo los `FeedFilters`)

Sin preferencias → una sola fase sin filtros geográficos.

### Ads

`get_ads` ([ads.py](backend/properties-service/src/app/services/search/helpers/feed/ads.py)):
- Sin preferencias → cache global `feed:ads:global`, miss → query `promoted_only=True`, cachea (TTL 1h).
- Con preferencias → cache por ciudad `feed:ads:<city_id>`; ciudades en miss se consultan y cachean.

### Paginación por cursor

`FeedCursor = (created_at, id, position)`. El repo usa `(cursor_created_at, cursor_id)` como keyset; `position` controla la rotación de ads y el corte de `FEED_MAX_RESULTS`.

## Feed mapa (`GetFeedMap`)

1. `bbox.to_polygon()` → `H3Shape`; `h3shape_to_cells(polygon, resolution, contain="center")` → lista de celdas.
2. **Cache-aside por celda**: `mget_json([map:h3:<cell>])`; las celdas hit se devuelven, las miss se acumulan.
3. Celdas miss → `properties.get_by_bbox(h3_indexes, resolution)` en Postgres.
4. Se cachean los resultados agrupados por celda (`mset_json`, TTL 5 min) y se devuelven `cached + fresh`.

Resolución elegida por el cliente vía query `resolution` (7–9): r9 (~300m) para zoom cercano, r7 (~5km) para zoom lejano. Ver [[adr-h3-dual-resolution-map]].

## Schemas

- `FeedPreferences` — `city_ids`, `neighborhood_ids`, `property_types`.
- `FeedFilters` — rangos de precio/área, `min_bathrooms`, `bedrooms`.
- `BoundingBox` — `min/max lat/lon`, con `to_polygon()`.
- `FeedCursor` — `created_at`, `id`, `position`.

Output uniforme: `list[PropertyCardSchema]`.

## Claims

- Cada página del feed son `FEED_PAGE_SIZE` resultados (default 20) con un ad cada `FEED_AD_INTERVAL` (default 5) ([settings.py:23-25](backend/properties-service/src/app/core/config/settings.py#L23-L25)).
- El feed corta y devuelve `[]` si `cursor.position >= FEED_MAX_RESULTS` (300) ([get_feed.py:24-25](backend/properties-service/src/app/services/search/use_cases/get_feed.py#L24-L25)).
- El orgánico degrada preferencias en 3 fases y devuelve la primera no vacía ([organic.py:32-41](backend/properties-service/src/app/services/search/helpers/feed/organic.py#L32-L41)).
- Los ads se cachean por ciudad (`feed:ads:<city_id>`) o globalmente (`feed:ads:global`) con TTL de 1h ([ads.py:12](backend/properties-service/src/app/services/search/helpers/feed/ads.py#L12), [cache_keys.py:12-17](backend/properties-service/src/app/services/shared/helpers/cache_keys.py#L12-L17)).
- El feed-mapa traduce el bbox a celdas H3 y aplica cache-aside por celda con clave `map:h3:<index>` ([get_feed_map.py:28-47](backend/properties-service/src/app/services/search/use_cases/get_feed_map.py#L28-L47)).
- La resolución del mapa está acotada a `[7, 9]` por el query param ([search.py:45](backend/properties-service/src/app/api/routes/search.py#L45)).
- El cache del mapa usa TTL de 5 minutos ([get_feed_map.py:14](backend/properties-service/src/app/services/search/use_cases/get_feed_map.py#L14)).
- El feed y el mapa son públicos — no hay dependency de auth en las rutas `/search/*` ([search.py:20-48](backend/properties-service/src/app/api/routes/search.py#L20-L48)).
