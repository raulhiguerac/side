---
title: ADR-0003 — POI cache-aside, never on-demand
status: stable
last-verified: 2026-05-21
owners: [catalog-service]
related:
  - "[[catalog-service-poi-lifecycle]]"
  - "[[catalog-service-architecture]]"
  - "[[glossary]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
decision-date: 2026-05-21
decision-status: accepted
---

# ADR-0003 — POI cache-aside, never on-demand

## Contexto

Los POIs (puntos de interés del entorno: escuelas, restaurantes, transporte) son útiles como features para el modelo AVM ([[avm-training]]) y eventualmente para enriquecer la UX del frontend ("hay 3 escuelas a 800 m"). La fuente externa es Overpass API (OpenStreetMap), que es **gratuita pero rate-limited y latente** (5-30s por query típica de bbox).

Dos preguntas de diseño:
1. ¿El frontend / un consumer puede pedir POIs en tiempo real (on-demand) o solo se sirven desde la BD local?
2. ¿Cuándo se invoca Overpass? ¿En cada request? ¿Vencimiento por TTL? ¿Background job?

## Decisión

- **POIs solo se sirven desde la BD local** — `points_of_interest` table. No hay endpoint público `/pois?near=...`.
- **Overpass se invoca SOLO como side-effect de un `geo-resolution`** — nunca on-demand desde un endpoint.
- **3 capas de dedup** para evitar fetches redundantes (ver [[catalog-service-poi-lifecycle]] para el diagrama):
  1. Redis cache short-circuit (`cache_key_fetch_zone`) — 30 días.
  2. Redis distributed lock (`SET NX`, TTL 30s) — evita races entre instancias.
  3. DB `FetchZone` freshness check — registra cada celda H3 res 9 ya consultada con timestamp.
- **Lazy-fill por tráfico**: las zonas se pueblan solo si alguien las "visita" georeferenciando un listing en ellas. Las zonas frías quedan vacías.
- **Refresh por staleness**: cuando una `FetchZone` excede `POI_STALE_THRESHOLD_DAYS` (30 d), el próximo geo-resolution la refetchea; o un batch nocturno (diseñado, **no implementado**) la marca para refresh.

## Alternativas consideradas

- **On-demand al request del frontend** — UX más rica ("acabamos de fetchear todos los POIs cerca!") pero hits a Overpass en el path crítico, latencia alta, rate-limit de Overpass se vuelve user-facing.
- **Pre-cargar el país entero** (batch one-shot) — costoso, mucho dato no usado, fácil de quedar stale.
- **Sin cache local, queries directas a Overpass** — viola los terms-of-use razonables del servicio gratuito.
- **Provider pago** (Foursquare Places, Mapbox POI) — costo + atadura comercial.

## Consecuencias

- ✅ Cero hits a Overpass en el path crítico del usuario.
- ✅ Dedup robusto: una zona caliente con N requests concurrentes hace un solo fetch.
- ✅ El dataset crece orgánicamente — solo se paga el costo donde hay tráfico real.
- ✅ Resiliente a Overpass down: las requests siguen funcionando contra POIs cached, solo la población de zonas nuevas se pausa.
- ❌ **Zonas frías quedan vacías** — si un dev quiere POIs de una región sin tráfico, no hay. Para training del AVM esto puede ser problema; hoy training usa CSV manual ([[avm-training]]) en parte por eso.
- ❌ **Batch de refresh no implementado al 2026-05-21** — las zonas stale solo se refrescan oportunísticamente.
- ❌ **Tag set de Overpass diverge de analytics ML** (~15 vs ~150 tags) — el side-effect actual no sirve completo al modelo. Conciliación pendiente.
- ❌ Lock distribuido depende de Redis — si Redis está down, hay riesgo de fetches concurrentes a la misma zona. Aceptable a escala actual (1 instancia del servicio).

## Claims

- `ResolvePoiUseCase` solo se invoca como `BackgroundTasks.add_task(...)`, nunca expuesto vía HTTP ([api/routes/geo_resolution.py:32-38](backend/catalog-service/src/app/api/routes/geo_resolution.py#L32-L38)).
- Las 3 capas de dedup: cache short-circuit, `set_nx` lock, `FetchZone` freshness ([resolve_poi.py:62-103](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_poi.py#L62-L103)).
- `POI_STALE_THRESHOLD_DAYS=30` y `POI_LOCK_TTL_SECONDS=30` ([core/config/settings.py:22-23](backend/catalog-service/src/app/core/config/settings.py#L22-L23)).
- Batch de refresh de zonas stale: **diseñado pero no implementado** al 2026-05-21.
- `FetchZone.is_stale=True` se setea automáticamente cuando una zona vencida es chequeada por el UC, pero ningún cron la dispara después.
