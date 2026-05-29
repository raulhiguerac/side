---
title: ADR-0004 — H3 dual-resolution para el feed-mapa
status: stable
last-verified: 2026-05-28
owners: [properties-service]
related: [[properties-service-search]], [[properties-service-architecture]], [[glossary]], [[adr-h3-resolution-per-use-case]]
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0004 — H3 dual-resolution para el feed-mapa

## Contexto

El feed-mapa devuelve las propiedades dentro del viewport del usuario. El viewport llega como bounding box `(min_lat, min_lon, max_lat, max_lon)` y cambia con cada pan/zoom. Dos requisitos en tensión: queries rápidas/cacheables, y soporte tanto de zoom cercano (una cuadra) como lejano (toda la ciudad). PostGIS ya tiene el POINT con índice GiST, así que ¿por qué agregar H3?

## Decisión

- **Indexar cada propiedad con dos celdas H3** precomputadas al crear/actualizar: `h3_r9` (~300m, vista de detalle/zoom cercano) y `h3_r7` (~5km, mapa zoomeado out).
- **El mapa resuelve por celdas, no por geometría cruda**: el bbox se convierte a polígono H3Shape y se expande a las celdas que contiene (`h3shape_to_cells`, `contain="center"`) en la resolución pedida.
- **Cache-aside por celda** (`map:h3:<index>`, TTL 5 min): cada celda es una unidad de cache independiente; el cliente que paneé a una zona ya vista pega 100% cache.
- **Resolución elegida por el cliente** vía query `resolution` (acotada a 7–9 según el nivel de zoom).

## Alternativas consideradas

- **Solo PostGIS `ST_Within(bbox)`** — funciona y el índice GiST es bueno, pero cada viewport es una geometría única → **incacheable** (la key sería el bbox exacto, que casi nunca se repite). H3 discretiza el espacio en celdas estables y reusables.
- **Una sola resolución H3** — r9 genera demasiadas celdas para un viewport de ciudad (miles de keys por request); r7 es muy grueso para el detalle. Dos resoluciones cubren ambos extremos de zoom.
- **Geohash en vez de H3** — equivalente conceptual, pero H3 ya se usa en [[catalog-service]] (POIs) y el ecosistema/tag set del proyecto es H3; consistencia.
- **Clustering server-side por densidad** — más sofisticado para mapas con miles de pines, pero overkill para MVP; las celdas H3 ya dan un agrupamiento natural.

## Consecuencias

- ✅ Viewports se vuelven cacheables: la unidad de cache es la celda, no el bbox.
- ✅ Pan/zoom sobre zonas ya vistas es casi todo cache hit.
- ✅ Dos resoluciones cubren detalle y ciudad sin un solo índice que sea malo en ambos extremos.
- ✅ Consistente con el uso de H3 en catalog-service.
- ❌ **Doble escritura**: cada create/update recomputa y guarda dos celdas; si la lógica de H3 cambia hay que re-backfillar ambas columnas.
- ❌ **Aliasing de bordes**: `contain="center"` puede incluir propiedades cuyo centro de celda cae dentro del bbox aunque el punto exacto esté justo afuera (y viceversa). Aceptable para un feed-mapa, no para queries de precisión.
- ❌ Solo dos niveles de zoom discretos — niveles intermedios reusan la celda más cercana, con sobre/sub-cobertura.
- ❌ Invalidar cache de mapa requiere conocer las celdas de la propiedad afectada (por eso `set_status` borra `map:h3:<r9>` y `map:h3:<r7>`).

## Claims

- `Property` guarda `h3_r9` y `h3_r7`, ambos indexados ([property.py:152-153](backend/properties-service/src/app/models/property.py#L152-L153)).
- Las celdas se computan con `h3.latlng_to_cell` en resoluciones 9 y 7 ([geometry.py:11-13](backend/properties-service/src/app/services/shared/helpers/geometry.py#L11-L13)).
- El feed-mapa convierte el bbox a celdas con `h3shape_to_cells_experimental(..., contain="center")` ([get_feed_map.py:28-29](backend/properties-service/src/app/services/search/use_cases/get_feed_map.py#L28-L29)).
- El cache de mapa es por celda con clave `map:h3:<index>` y TTL de 5 min ([get_feed_map.py:14](backend/properties-service/src/app/services/search/use_cases/get_feed_map.py#L14), [cache_keys.py:20-21](backend/properties-service/src/app/services/shared/helpers/cache_keys.py#L20-L21)).
- La resolución del mapa está acotada a `[7, 9]` ([search.py:45](backend/properties-service/src/app/api/routes/search.py#L45)).
- `set_status` invalida las celdas H3 de la propiedad al cambiar status ([set_status.py:50-54](backend/properties-service/src/app/services/admin/use_cases/moderation/set_status.py#L50-L54)).
