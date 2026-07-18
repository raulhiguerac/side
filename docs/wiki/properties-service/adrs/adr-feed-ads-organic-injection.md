---
title: ADR-0002 — Feed = orgánico + ads intercalados con fallback de preferencias
status: stable
last-verified: 2026-07-13
owners: [properties-service]
related:
  - "[[properties-service-search]]"
  - "[[properties-service-architecture]]"
  - "[[adr-feed-opaque-cursor]]"
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0002 — Feed = orgánico + ads intercalados con fallback de preferencias

## Contexto

El feed público debe (a) monetizar vía promociones pagas, (b) respetar preferencias del usuario (ciudad/barrio/tipo) sin dejar la pantalla vacía cuando no hay match exacto, y (c) paginar de forma estable a medida que entran/salen listings.

## Decisión

- **Composición orgánico + ads por página**: cada página son `FEED_PAGE_SIZE` (20) resultados; se reserva espacio para `min(len(ads), page_size // FEED_AD_INTERVAL)` promociones y el resto es orgánico. Los ads se **intercalan** uno cada `FEED_AD_INTERVAL` (5) posiciones orgánicas, con un punto de arranque que rota según la posición del cursor.
- **Fallback de preferencias por fases**: si el usuario tiene `preferences`, el orgánico intenta hasta 3 niveles de relajación y devuelve el primero no vacío:
  1. barrio + ciudad + tipo
  2. ciudad + tipo (sin barrio)
  3. sin filtros de preferencia
  Si el usuario **no tiene preferences** (`None`), no hay 3 fases que probar — corre directo una única query sin filtros, funcionalmente equivalente a caer en la fase 3.
- **Ads cacheados aparte**: por ciudad (`feed:ads:<city_id>`) o globalmente (`feed:ads:global`), TTL 1h — las promociones cambian lento comparado con el orgánico.
- **Paginación por cursor** `(created_at, id, position)`: keyset sobre `(created_at, id)` para estabilidad; `position` controla rotación de ads y el corte en `FEED_MAX_RESULTS` (300).

## Alternativas consideradas

- **OFFSET/LIMIT** — simple, pero inestable: insertar/borrar listings desplaza páginas y duplica/saltea resultados. Descartado por keyset cursor.
- **Ads como query unificada** (orgánico y promovidos en un solo SELECT con ORDER BY priority) — más simple, pero acopla el ritmo de inyección a la query y complica cachear ads por separado.
- **Sin fallback** (solo match exacto de preferencias) — feed vacío frecuente para usuarios con preferencias estrechas; mala primera impresión.
- **Ranking ML/personalización** — fuera de scope MVP; el fallback por fases es un proxy barato y explicable.

## Consecuencias

- ✅ Monetización integrada sin una segunda query en el path caliente (ads vienen de cache la mayoría del tiempo).
- ✅ Desde 2026-06-08 la página completa de orgánico (cards + cursor) también tiene cache-aside en Redis, key `feed:page:{hash(cursor, preferences, filters)}`, TTL `FEED_PAGE_CACHE_TTL_SECONDS` (300s) — los ads se re-obtienen frescos en cada hit para preservar la rotación (ver [[adr-feed-opaque-cursor]]).
- ✅ El feed casi nunca queda vacío gracias al fallback.
- ✅ Paginación estable bajo escritura concurrente.
- ✅ Densidad de ads acotada y predecible (1 cada 5).
- ❌ El fallback puede devolver resultados poco relevantes (fase 3 = cualquier cosa) sin señalizar al usuario que se relajó el filtro.
- ❌ Cache de ads con TTL de 1h → una promo recién creada puede tardar hasta 1h en aparecer (mitigable invalidando la key al crear/borrar promo).
- ❌ La rotación de ads por `position` es determinística, no aleatoria — patrón potencialmente repetitivo para el usuario que scrollea mucho.

## Claims

- `FEED_PAGE_SIZE=20`, `FEED_MAX_RESULTS=300`, `FEED_AD_INTERVAL=5` ([settings.py:26-28](backend/properties-service/src/app/core/config/settings.py#L26-L28)).
- Los ads por página son `min(len(ads), page_size // ad_interval)` ([get_feed.py:56](backend/properties-service/src/app/services/search/use_cases/get_feed.py#L56)).
- El orgánico prueba 3 fases de preferencias y devuelve la primera no vacía **solo si `preferences` no es `None`**; sin preferences corre una única query sin filtros ([organic.py:34-45](backend/properties-service/src/app/services/search/helpers/feed/organic.py#L34-L45), [organic.py:47-63](backend/properties-service/src/app/services/search/helpers/feed/organic.py#L47-L63)).
- Los ads se cachean por ciudad o globalmente con TTL de 3600s ([ads.py:12](backend/properties-service/src/app/services/search/helpers/feed/ads.py#L12)).
- El cursor `(created_at, id, position)` corta en `FEED_MAX_RESULTS` ([get_feed.py:29-31](backend/properties-service/src/app/services/search/use_cases/get_feed.py#L29-L31)).
