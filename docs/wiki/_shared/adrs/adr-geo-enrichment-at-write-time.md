---
title: ADR-0002 — Geo-enrichment at write time
status: stable
last-verified: 2026-06-20
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[analytics-service-prediction]]"
  - "[[glossary]]"
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
decision-date: 2026-05-19
decision-status: accepted
---

# ADR-0002 — Geo-enrichment at write time

## Contexto

Los listings tienen `lat/lon`. Múltiples consumidores necesitan derivados geográficos del listing: el feed filtra por barrio, `analytics-service` lo usa como feature del modelo, el heatmap del dominio market lo agrega, los reportes B2B lo segmentan. La resolución `(lat, lon) → barrio_ideca` (estándar [[glossary#ideca]]) requiere un spatial lookup contra un dataset con miles de polígonos.

¿Dónde y cuándo se hace ese lookup?

## Decisión

La resolución de `barrio_ideca` ocurre **al crear el listing en `properties-service`**, no en cada consumidor cuando lo necesita. El valor se persiste en la fila del listing y se propaga río abajo (en requests HTTP, mensajes async, etc.). Los consumidores reciben el valor ya resuelto y **no re-resuelven**.

## Alternativas consideradas

- **At read time**: cada servicio resuelve cuando lo necesita. Simple pero N veces más spatial lookups, latencia en path crítico de lectura, sin posibilidad de cachear/indexar por barrio.
- **Dedicated geo-service** que cualquier servicio llame on-demand. Centralización limpia pero un round-trip extra por cada listing en cada operación.
- **Compute on the client** (frontend) usando Mapbox/Google Geocoding — exposición de claves API + costo por request al provider + posible inconsistencia entre clientes.

## Consecuencias

- ✅ Cero spatial lookups en el path crítico de lectura — feeds y predicciones rápidos.
- ✅ Indexable y cacheable por `barrio_ideca` en BD.
- ✅ Cada consumidor confía en el valor sin re-resolver — contrato simple.
- ✅ Una sola implementación del geocoding en todo el sistema (`properties-service`).
- ❌ Si IDECA cambia un boundary, todos los listings quedan con barrio stale hasta un backfill explícito.
- ❌ La latencia de creación de listing aumenta por el spatial lookup.
- ❌ Si el geocoding falla, no se puede crear el listing — accept-vs-reject trade-off.

## Claims

- `analytics-service` recibe `barrio_ideca` en `PredictionRequest` y nunca hace geocoding ([schemas/prediction.py:21](backend/analytics-service/src/app/services/prediction/schemas/prediction.py#L21)).
- `PredictionRequest.barrio_ideca` solo valida `min_length=1`; no se chequea contra ningún catálogo en `analytics-service`.
- El geocoder real vive en `properties-service` (o eventualmente `catalog-service`) — no en `analytics-service`.
