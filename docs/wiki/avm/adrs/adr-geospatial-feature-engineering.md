---
title: ADR-0003 — Feature engineering geoespacial schema-driven
status: stable
last-verified: 2026-07-15
owners: [data]
related:
  - "[[avm-training]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[catalog-service-overpass]]"
  - "[[glossary]]"
  - "[[adr-h3-resolution-per-use-case]]"
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0003 — Feature engineering geoespacial schema-driven

## Contexto

En real estate, **la ubicación domina el precio**. Un modelo con solo atributos del inmueble (área, cuartos, estrato) deja fuera la señal más fuerte: qué hay alrededor. Hay que codificar el entorno geográfico de cada listing como features, de forma estable, reproducible y versionable, sin que un cambio de features obligue a reescribir el pipeline.

## Decisión

Tres familias de features geoespaciales, más un schema externo que parametriza todo:

- **H3 multi-resolución**: cada listing se indexa en celdas H3 en resoluciones 6, 7 y 8 (`h3_r6/r7/r8`) — captura el "barrio" a tres granularidades como categóricas.
- **Conteo de POIs por radio y categoría**: para 3 radios (300m, 800m, 1200m) y ~15 categorías (transporte, comida, educación, salud, etc.), se cuenta cuántos POIs hay cerca (`poi_<radio>_<cat>`), usando un `BallTree(haversine)`. Los POIs vienen hoy de un CSV de OpenStreetMap.
- **Distancias a landmarks**: distancia haversine a 12 landmarks de Bogotá hardcodeados (centros comerciales, portales TM, universidades, parques, aeropuerto) → 12 features `dist_<landmark>`.
- **Schema-driven**: un JSON externo (`--feature-schema-path`) declara features, categóricas, target y validaciones. El pipeline se parametriza por ese schema; agregar/quitar features no requiere tocar el código de orquestación.
- **Auditoría**: el `md5` del archivo de POIs se loguea como `poi_md5` en cada run, para saber contra qué POIs se entrenó cada modelo.

## Alternativas consideradas

- **Solo lat/lon crudos** — los árboles no extraen bien la señal espacial de coordenadas en bruto; H3 + features derivadas la hacen explícita.
- **Una sola resolución H3** — un solo nivel pierde o el detalle de cuadra o el contexto de zona; tres niveles cubren el rango.
- **POIs en tiempo real desde Overpass** — latencia y rate-limits inaceptables en training; se usa un snapshot CSV (y a futuro la tabla de [[catalog-service-poi-lifecycle]]).
- **Features hardcodeadas en el código** — cada cambio de features sería un cambio de código; el schema JSON desacopla el contrato de features de la implementación.

## Consecuencias

- ✅ Codifica la señal dominante (ubicación) de forma rica y explícita.
- ✅ H3 multi-res da contexto a varias escalas sin coordenadas crudas.
- ✅ El schema JSON permite versionar el contrato de features sin reescribir el pipeline.
- ✅ `poi_md5` da trazabilidad de qué datos de entorno produjeron cada modelo.
- ❌ **Tag set de POIs diverge del de [[catalog-service-overpass]]** (~15 categorías del training vs el tag set que catalog extrae) — el feature store del servicio no alimenta directamente el training hoy; conciliación pendiente.
- ❌ **POIs por CSV manual** — no reproducible automáticamente; depende de un export externo (futuro: tabla de catalog → DWH).
- ❌ **Landmarks hardcodeados y Bogotá-específicos** — el modelo no generaliza a otras ciudades sin re-hardcodear landmarks y recalibrar.
- ❌ El conteo de POIs por `BallTree` se recomputa en cada fit; a mayor escala de POIs puede volverse costoso.

## Claims

- Se generan celdas H3 en resoluciones 6, 7 y 8 ([feature_store/constants.py:31](data/ml/AVM/training/feature_store/constants.py#L31)).
- Los POIs se cuentan en 3 radios — 300m, 800m, 1200m — por categoría ([feature_store/constants.py:33](data/ml/AVM/training/feature_store/constants.py#L33), [transforms/poi.py](data/ml/AVM/training/transforms/poi.py)).
- Hay 12 landmarks de Bogotá hardcodeados que producen 12 features `dist_<landmark>` ([feature_store/constants.py:3-16](data/ml/AVM/training/feature_store/constants.py#L3-L16)).
- El pipeline se parametriza por un JSON de schema (`--feature-schema-path`) con features, cat_cols, target y validaciones ([train.py](data/ml/AVM/training/train.py)).
- El `poi_md5` se loguea como param en cada run para auditar la fuente de POIs ([trainer.py:90](data/ml/AVM/training/pipeline/trainer.py#L90)).
- El tag set de POIs del training (~15 categorías) diverge del de catalog-service — conciliación pendiente ([[catalog-service-overpass]]).
