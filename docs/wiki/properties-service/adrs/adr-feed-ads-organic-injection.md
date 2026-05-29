---
title: ADR-0002 — Feed = orgánico + ads intercalados con fallback de preferencias
status: stable
last-verified: 2026-05-28
owners: [properties-service]
related: [[properties-service-search]], [[properties-service-architecture]]
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0002 — Feed = orgánico + ads intercalados con fallback de preferencias

## Contexto

El feed público debe (a) monetizar vía promociones pagas, (b) respetar preferencias del usuario (ciudad/barrio/tipo) sin dejar la pantalla vacía cuando no hay match exacto, y (c) paginar de forma estable a medida que entran/salen listings.

## Decisión

- **Composición orgánico + ads por página**: cada página son `FEED_PAGE_SIZE` (20) resultados; se reserva espacio para `min(len(ads), page_size // FEED_AD_INTERVAL)` promociones y el resto es orgánico. Los ads se **intercalan** uno cada `FEED_AD_INTERVAL` (5) posiciones orgánicas, con un punto de arranque que rota según la posición del cursor.
- **Fallback de preferencias por fases**: el orgánico intenta hasta 3 niveles de relajación y devuelve el primero no vacío:
  1. barrio + ciudad + tipo
  2. ciudad + tipo (sin barrio)
  3. sin filtros de preferencia
- **Ads cacheados aparte**: por ciudad (`feed:ads:<city_id>`) o globalmente (`feed:ads:global`), TTL 1h — las promociones cambian lento comparado con el orgánico.
- **Paginación por cursor** `(created_at, id, position)`: keyset sobre `(created_at, id)` para estabilidad; `position` controla rotación de ads y el corte en `FEED_MAX_RESULTS` (300).

## Alternativas consideradas

- **OFFSET/LIMIT** — simple, pero inestable: insertar/borrar listings desplaza páginas y duplica/saltea resultados. Descartado por keyset cursor.
- **Ads como query unificada** (orgánico y promovidos en un solo SELECT con ORDER BY priority) — más simple, pero acopla el ritmo de inyección a la query y complica cachear ads por separado.
- **Sin fallback** (solo match exacto de preferencias) — feed vacío frecuente para usuarios con preferencias estrechas; mala primera impresión.
- **Ranking ML/personalización** — fuera de scope MVP; el fallback por fases es un proxy barato y explicable.

## Consecuencias

- ✅ Monetización integrada sin una segunda query en el path caliente (ads vienen de cache la mayoría del tiempo).
- ✅ El feed casi nunca queda vacío gracias al fallback.
- ✅ Paginación estable bajo escritura concurrente.
- ✅ Densidad de ads acotada y predecible (1 cada 5).
- ❌ El fallback puede devolver resultados poco relevantes (fase 3 = cualquier cosa) sin señalizar al usuario que se relajó el filtro.
- ❌ Cache de ads con TTL de 1h → una promo recién creada puede tardar hasta 1h en aparecer (mitigable invalidando la key al crear/borrar promo).
- ❌ La rotación de ads por `position` es determinística, no aleatoria — patrón potencialmente repetitivo para el usuario que scrollea mucho.

## Claims

- `FEED_PAGE_SIZE=20`, `FEED_MAX_RESULTS=300`, `FEED_AD_INTERVAL=5` ([settings.py:23-25](backend/properties-service/src/app/core/config/settings.py#L23-L25)).
- Los ads por página son `min(len(ads), page_size // ad_interval)` ([get_feed.py:32-33](backend/properties-service/src/app/services/search/use_cases/get_feed.py#L32-L33)).
- El orgánico prueba 3 fases de preferencias y devuelve la primera no vacía ([organic.py:32-60](backend/properties-service/src/app/services/search/helpers/feed/organic.py#L32-L60)).
- Los ads se cachean por ciudad o globalmente con TTL de 3600s ([ads.py:12](backend/properties-service/src/app/services/search/helpers/feed/ads.py#L12)).
- El cursor `(created_at, id, position)` corta en `FEED_MAX_RESULTS` ([get_feed.py:24-25](backend/properties-service/src/app/services/search/use_cases/get_feed.py#L24-L25)).
