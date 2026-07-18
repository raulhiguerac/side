---
title: AVM Predict Endpoint — Estado backend y diseño del form frontend
captured-from: conversation
captured-on: 2026-05-26
participants: [raul, claude]
---

## Context
Se revisó el estado real del analytics-ms y se diseñó el form frontend para el endpoint `/v1/predict`. El backend resultó estar 100% completo; la discusión se centró en el diseño del form y la decisión de persistir la dirección.

## Key conclusions
- **Backend completo**: `POST /v1/predict` wired — router, DI (`deps/prediction.py`), `OnlinePrediction` UC, `AVMModelAdapter` → MLflow `bogota-avm@production`, Alembic migration para tabla `predictions`.
- **Form frontend — 7 campos visibles**: dirección (Mapbox autocomplete), tipo (apartment | house), área m², habitaciones, baños, parqueaderos, estrato (1-6), año construcción (opcional).
- **`lat`, `lon`, `barrio_ideca` son transparentes al usuario**: resueltos vía chain de 3 pasos: (1) Mapbox geocode → lat/lon, (2) `GET /v1/geo-resolution/by-coordinates?lat=&lon=` en catalog-ms → barrio_ideca, (3) `POST /v1/predict` en analytics-ms.
- **Decisión: guardar la dirección** — agregar `address: Optional[str] = None` a `PredictionRequest` + columna en la migración. Habilita historial de avalúos y analytics de zonas consultadas sin romper el flujo actual. `address` se excluye del `model_dump` que va al modelo ML (no es feature).
- **Resultado visible**: precio estimado + `model_version` + disclaimer de margen (<11% error medio).

## Open questions
- Ninguna — diseño acordado.

## Next steps
- Agregar `address: Optional[str]` a `PredictionRequest` + nueva migración Alembic con la columna.
- Construir componente de form frontend con Mapbox autocomplete + chain de 3 llamadas.
- Mostrar resultado: precio + versión del modelo + disclaimer.
