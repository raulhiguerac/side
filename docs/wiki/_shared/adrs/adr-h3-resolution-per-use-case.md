---
title: ADR-0003 — Resolución H3 por caso de uso, celdas no reusables entre fronteras
status: stable
last-verified: 2026-05-28
owners: [_shared, data, properties-service, catalog-service]
related: [[architecture]], [[glossary]], [[adr-h3-dual-resolution-map]], [[adr-geospatial-feature-engineering]], [[adr-postgis-h3-hybrid]], [[avm-training]]
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0003 — Resolución H3 por caso de uso, celdas no reusables entre fronteras

## Contexto

[[glossary#h3|H3]] se usa en tres lugares del sistema con **resoluciones distintas**:

| Dónde | Resoluciones | Para qué |
|---|---|---|
| `properties-service` | r9 (~300 m), r7 (~5 km) | bucketing del feed-mapa por bbox |
| `catalog-service` | r9 (~300 m) | índice de polígonos de barrios + zonas de fetch de POIs |
| AVM (modelo) | r6, r7, r8 | features del vector del modelo |

A primera vista parece una inconsistencia (un servicio guarda r9, el modelo entrena en r8). La pregunta: ¿se debe unificar la resolución, o la divergencia es correcta? Y si es correcta, ¿qué garantía hay que mantener para que no se rompa cuando se integren los lados (p. ej. alimentar el feature store de un MS al modelo)?

## Decisión

- **La resolución H3 se elige por caso de uso, no globalmente.** Los dos usos son fundamentalmente distintos:
  - **En un servicio, H3 es una clave de lookup espacial.** Una query indexada sobre la celda devuelve la lista de entidades en ella. Conviene **granular (r9)**: celdas chicas → resultados acotados y precisos para el viewport/zona. properties agrega r7 para el zoom lejano del mapa.
  - **En el modelo, H3 es un feature del vector.** Conviene **más grueso (r6/r7/r8)**: r9 haría cada celda casi única → señal dispersa, ruido y riesgo de overfitting. Resoluciones gruesas agrupan zonas con señal de precio compartida.
- **Las celdas NO se cruzan entre fronteras.** El modelo **recomputa** sus celdas r6/r7/r8 desde `lat/lon` en inferencia (en el preprocesador del AVM); **nunca** consume las celdas r9/r7 que almacenan los servicios. Los servicios, a su vez, no usan las celdas del modelo.
- **Garantía a mantener**: cualquier integración que cruce el límite servicio↔modelo (ej. cuando el feature store de catalog/properties alimente al AVM) **debe recomputar la resolución del consumidor desde `lat/lon`**, no reusar la celda almacenada del productor.

## Alternativas consideradas

- **Una sola resolución global** (todo en r9, o todo en r8). Sería joinable y simple, pero fuerza un compromiso malo para un lado: r9 mete ruido como feature del modelo; r6/r8 son demasiado gruesos para un lookup espacial útil en el mapa. Optimizar para ambos a la vez no existe en una sola resolución.
- **Estandarizar en las resoluciones del modelo (6/7/8) en los servicios.** Los servicios no necesitan tres niveles y el lookup de mapa en r6 sería inútilmente grueso.
- **Dejar la divergencia implícita** (sin documentar). Riesgo concreto: alguien asume que las celdas almacenadas son reusables entre fronteras y hace un join que silenciosamente no alinea (r9 ≠ r8; r6/r8 no existen en los MS).

## Consecuencias

- ✅ Cada caso de uso obtiene la resolución óptima: lookups espaciales granulares en los servicios, features sin sobre-granularidad en el modelo.
- ✅ Hoy **no hay bug**: el modelo es autosuficiente (recomputa desde `lat/lon`), así que la divergencia no afecta predicciones.
- ✅ La garantía "recomputar, no reusar" deja el contrato explícito para la integración futura del feature store.
- ❌ **Varios regímenes de resolución** en el código → carga cognitiva; no hay una constante compartida que documente el mapeo (vive en este ADR + [[glossary#h3]]).
- ❌ **r7 se solapa por coincidencia** entre properties (mapa zoom-out) y el modelo (feature), con propósitos distintos — puede inducir a pensar que son intercambiables. No lo son.
- ❌ Si en el futuro se quisiera **sí** reusar celdas entre fronteras (por performance), habría que introducir una resolución compartida y revisar esta decisión.

## Open items

- Cuando se cablee el feature store desde un MS hacia el AVM (ver [[adr-geospatial-feature-engineering]] y el open item de tag set de POIs), validar que la resolución se recomputa del lado del modelo.
- Evaluar extraer las resoluciones a una constante/config compartida si el mapeo crece o se vuelve confuso.

## Claims

- El AVM define `H3_RESOLUTIONS = [6, 7, 8]` para sus features ([feature_store/constants.py:31](data/ml/AVM/training/feature_store/constants.py#L31)).
- properties-service computa H3 en resoluciones 9 y 7 (`h3_r9`, `h3_r7`) ([geometry.py:11-13](backend/properties-service/src/app/services/shared/helpers/geometry.py#L11-L13)).
- catalog-service usa `H3_RESOLUTION = 9` ([core/config/settings.py:24](backend/catalog-service/src/app/core/config/settings.py#L24)) y precomputa `FetchZone.h3_index` en res 9 ([models/location.py:375](backend/catalog-service/src/app/models/location.py#L375)).
- El AVM recomputa sus celdas H3 desde `lat/lon` en el preprocesador (`add_h3`), no las recibe del caller ([[avm-training]]).
- El adapter de analytics pasa el request crudo (lat/lon) al modelo, sin celdas H3 ([[avm-training]]).
- Ningún servicio almacena celdas en r6 ni r8; el modelo ignora las celdas r9 de los servicios.
