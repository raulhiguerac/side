---
title: Dominio search — properties-service
status: stable
last-verified: 2026-08-01
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[properties-service-architecture]]"
  - "[[adr-feed-ads-organic-injection]]"
  - "[[adr-feed-opaque-cursor]]"
  - "[[adr-h3-dual-resolution-map]]"
  - "[[frontend-architecture]]"
  - "[[open-items]]"
  - "[[properties-service-admin]]"
  - "[[properties-service-bulk-create-worker]]"
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md, ../../../sources/_shared/2026-05-31-impressions-feed-personalization-supply.md, ../../../sources/frontend/2026-06-04-feed-filters-contract.md, ../../../sources/properties-service/2026-06-05-feed-cursor-pagination.md, ../../../sources/properties-service/2026-06-08-feed-cache-geo-scaling.md, ../../../sources/properties-service/2026-08-01-bulk-import-pending-verification.md]
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

Corte duro: si `cursor.position >= FEED_MAX_RESULTS` (300) → devuelve `FeedPage(items=[], next_cursor=None)`.

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

El cursor es **opaco**: `FeedCursor(created_at, id, position)` se serializa como `JSON → UTF-8 → base64url` y se devuelve al cliente como `next_cursor: str | None` dentro de `FeedPage`. El cliente lo reenvía como `?cursor=<token>` sin conocer su estructura interna. Ver [[adr-feed-opaque-cursor]].

- El repo usa `(cursor_created_at, cursor_id)` como keyset (`created_at < last_seen`), garantizando estabilidad aunque entren propiedades nuevas al top del feed.
- `position` cuenta solo orgánicos (no ads) y sirve para el corte `FEED_MAX_RESULTS` y la rotación de ads.
- Cuando no hay más resultados, el UC devuelve `FeedPage(items=[], next_cursor=None)`.
- El cursor se decodifica en el UC (`decode_cursor`); un token corrupto lanza `InvalidCursorError` → HTTP 400.
- `parse_feed_cursor` (dep de 3 params separados) fue eliminado; el endpoint recibe `cursor: Optional[str] = Query(default=None)` directamente.

### Cache de página (Redis cache-aside)

`GetFeedUseCase` aplica cache-aside **solo sobre los orgánicos** antes de consultar la DB:

1. Construye `cache_key = feed_page(cursor_str, preferences=..., filters=...)`.
2. Si hay hit en Redis → restaura `cards` con `model_validate`, re-inyecta ads (ads no se cachean para preservar rotación), retorna `FeedPage` sin tocar la DB.
3. Si miss → ejecuta `get_organic` + `_inject_ads` como siempre, luego cachea `{"items": [c.model_dump(mode="json")], "next_cursor": ...}` con `TTL = FEED_PAGE_CACHE_TTL_SECONDS` (300 s, 5 min).

**Por qué `model_dump(mode="json")`**: los cards tienen campos `Decimal` (precio) y `UUID` que `json.dumps` no serializa sin `default=str`; `mode="json"` resuelve esto nativamente dentro de Pydantic.

**Cache key collision-safe**: la key no es solo el cursor — incluye un hash `sha256[:16]` de `{cursor, preferences, filters}`. Sin esto dos usuarios con preferencias distintas pero en la misma página `"first"` colisionan en la misma key.

```python
# cache_keys.py
def _short_hash(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def feed_page(cursor_str: str | None, preferences: Any = None, filters: Any = None) -> str:
    payload = {"cursor": cursor_str, "preferences": preferences, "filters": filters}
    return f"feed:page:{_short_hash(payload)}"
```

No hay invalidación proactiva — el TTL de 5 min es suficiente para este workload de lectura (consistencia eventual aceptable). Los ads se omiten del cache deliberadamente: se re-inyectan siempre en fresco para que la rotación no quede congelada.

## Feed mapa (`GetFeedMap`)

1. `bbox.to_polygon()` → `h3.LatLngPoly`; `h3shape_to_cells(polygon, resolution, contain="center")` → lista de celdas.

> ✅ **Bug corregido (2026-06-09)**: `to_polygon()` instanciaba `h3.H3Shape(...)`, la clase abstracta padre de `LatLngPoly`/`LatLngMultiPoly` (no instanciable) — `GetFeedMapUseCase` crasheaba en runtime. Fix aplicado: `h3.LatLngPoly(...)`. Ver [[open-items]].

2. **Cache-aside por celda**: `mget_json([map:h3:<cell>])`; las celdas hit se devuelven, las miss se acumulan.
3. Celdas miss → `properties.get_by_bbox(h3_indexes, resolution)` en Postgres. El repo filtra **solo por columna H3** (`h3_r7.in_(cells)` o `h3_r9.in_(cells)` según la resolución) — no hay `ST_Within` en este path; la precisión del bbox es la de las celdas (`contain="center"`).
4. Se cachean los resultados agrupados por celda (`mset_json`, TTL 5 min) y se devuelven `cached + fresh`.

Resolución elegida por el cliente vía query `resolution` (7–9): r9 (~300m) para zoom cercano, r7 (~5km) para zoom lejano. Ver [[adr-h3-dual-resolution-map]].

## Schemas

- `FeedPreferences` — `city_ids`, `neighborhood_ids`, `property_types`.
- `FeedFilters` — rangos de precio/área, `min_bathrooms`, `bedrooms`.
- `BoundingBox` — `min/max lat/lon`, con `to_polygon()`.
- `FeedCursor` — `created_at`, `id`, `position`. Opaco para el cliente (base64url).
- `FeedPage` — `items: list[PropertyCardSchema]`, `next_cursor: str | None = None`. Respuesta del feed.

`get_organic` retorna `tuple[list[PropertyCardSchema], tuple[datetime, UUID] | None]`; el segundo elemento es `(last.created_at, last.id)` del último resultado ORM antes de validar, o `None` si no hay resultados.

`PropertyCardSchema` **no lleva `verification_status`**, así que ni el feed ni el feed-mapa pueden mostrar si un listing está en revisión. El detalle público sí lo hace (`usePropertyDetail` mapea `pending → "En revisión"` y `PropertyOverview` lo renderiza), con lo cual el aviso existe recién después de clickear. Importa desde que el import masivo entra en `pending` con `status=active` (ver [[properties-service-admin]], [[properties-service-bulk-create-worker]]): la posición tomada es publicar avisando, y el aviso falta justo donde la gente navega. Registrado en [[open-items]].

`FeedPreferences` y `FeedFilters` son ambos opcionales: los deps `parse_feed_preferences` / `parse_feed_filters` devuelven `None` si no llega nada. En el repo, `get_properties` aplica **cada filtro de forma independiente** con un `if x is not None` separado, así que filtros parciales funcionan — mandar solo `max_price` agrega solo `WHERE price <= max_price` sin tocar el resto. Sin preferencias ni filtros, el feed no aplica ningún `WHERE` adicional (más allá de `active` + no borrado).

## Evolución planeada del feed

El feed hoy filtra por **preferencias declaradas** (onboarding: barrios, ciudades, tipo de propiedad). La evolución planeada tiene dos capas:

1. **Señales implícitas de comportamiento** — impresiones (qué listings vio el usuario), tiempo de vista y retorno. Se capturarían como evento Kafka `listing.impressed` consumido por analytics-ms para alimentar un recomendador colaborativo o content-based que mejore el ranking orgánico.
2. **Señal geoespacial del mapa** — el bbox del mapa estilo Airbnb revela la zona de interés sin acción explícita; puede alimentar el recomendador directamente.

El promoted targeting también evoluciona: hoy los ads son globales o por ciudad; con historial de impresiones se pueden dirigir a perfiles con mayor probabilidad de conversión. Ver [[open-items]] para los ítems pendientes.

## Claims

- `PropertyCardSchema` no incluye `verification_status`, así que las respuestas de `/search/feed` y `/search/feed/map` no lo transportan ([property_card.py](backend/properties-service/src/app/services/shared/schemas/property_card.py)).
- Cada página del feed son `FEED_PAGE_SIZE` resultados (default 20) con un ad cada `FEED_AD_INTERVAL` (default 5) ([settings.py:23-25](backend/properties-service/src/app/core/config/settings.py#L23-L25)).
- El feed devuelve `FeedPage(items=[], next_cursor=None)` si `cursor.position >= FEED_MAX_RESULTS` (300) ([get_feed.py:29-30](backend/properties-service/src/app/services/search/use_cases/get_feed.py#L29-L30)).
- El endpoint `/search/feed` devuelve `FeedPage` (`items` + `next_cursor: str | None`); ya no devuelve `list[PropertyCardSchema]` ([search.py:21](backend/properties-service/src/app/api/routes/search.py#L21)).
- El cursor se transporta como un único query param `?cursor=<base64url>` en lugar de tres params separados ([search.py:28](backend/properties-service/src/app/api/routes/search.py#L28)).
- `decode_cursor` lanza `InvalidCursorError` (HTTP 400) ante cualquier fallo de decodificación o validación ([encoding.py:12-18](backend/properties-service/src/app/services/search/helpers/feed/encoding.py#L12-L18)).
- `get_organic` retorna `(cards, (last.created_at, last.id))` o `([], None)` si no hay resultados ([organic.py:40-45](backend/properties-service/src/app/services/search/helpers/feed/organic.py#L40-L45)).
- `position` en el cursor cuenta solo orgánicos; los ads inyectados no se suman ([get_feed.py:58-60](backend/properties-service/src/app/services/search/use_cases/get_feed.py#L58-L60)).
- El orgánico degrada preferencias en 3 fases y devuelve la primera no vacía ([organic.py:32-45](backend/properties-service/src/app/services/search/helpers/feed/organic.py#L32-L45)).
- Los ads se cachean por ciudad (`feed:ads:<city_id>`) o globalmente (`feed:ads:global`) con TTL de 1h ([ads.py:12](backend/properties-service/src/app/services/search/helpers/feed/ads.py#L12), [cache_keys.py:12-17](backend/properties-service/src/app/services/shared/helpers/cache_keys.py#L12-L17)).
- El feed-mapa traduce el bbox a celdas H3 y aplica cache-aside por celda con clave `map:h3:<index>` ([get_feed_map.py:28-47](backend/properties-service/src/app/services/search/use_cases/get_feed_map.py#L28-L47)).
- La resolución del mapa está acotada a `[7, 9]` por el query param ([search.py:45](backend/properties-service/src/app/api/routes/search.py#L45)).
- El cache del mapa usa TTL de 5 minutos ([get_feed_map.py:14](backend/properties-service/src/app/services/search/use_cases/get_feed_map.py#L14)).
- El feed y el mapa son públicos — no hay dependency de auth en las rutas `/search/*` ([search.py:20-48](backend/properties-service/src/app/api/routes/search.py#L20-L48)).
- `get_properties` aplica cada filtro (`min_price`, `max_price`, `min_area_m2`, `max_area_m2`, `min_bathrooms`, `bedrooms`) con un `if x is not None` independiente, por lo que los filtros parciales son válidos ([sql_property_search_repository.py:54-70](backend/properties-service/src/app/services/search/adapters/sql_property_search_repository.py#L54-L70)).
- `BoundingBox.to_polygon()` instancia `h3.H3Shape(...)`, una clase abstracta no instanciable — el feed-mapa tiene un bug latente hasta migrar a `h3.LatLngPoly(...)` ([feed_schemas.py:31-32](backend/properties-service/src/app/services/search/schemas/feed_schemas.py#L31-L32)).
- `GetFeedUseCase` aplica cache-aside Redis sobre los orgánicos: hit → restaura cards + re-inyecta ads en fresco; miss → fetch DB + cachea items serializados ([get_feed.py](backend/properties-service/src/app/services/search/use_cases/get_feed.py)).
- Cache key del feed: `feed:page:{sha256[:16](json({cursor, preferences, filters}))}` — incluye el hash de preferencias y filtros para evitar colisiones entre usuarios en la misma página ([cache_keys.py](backend/properties-service/src/app/services/shared/helpers/cache_keys.py)).
- `FEED_PAGE_CACHE_TTL_SECONDS = 300` (5 min) — los ads no se cachean; se re-inyectan en cada request para preservar rotación ([settings.py](backend/properties-service/src/app/core/config/settings.py)).
- `model_dump(mode="json")` es obligatorio para serializar cards a Redis — los campos `Decimal` y `UUID` fallan con `json.dumps` sin `default=str` ([get_feed.py](backend/properties-service/src/app/services/search/use_cases/get_feed.py)).
