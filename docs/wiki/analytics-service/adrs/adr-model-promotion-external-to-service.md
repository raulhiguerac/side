---
title: ADR-0003 — Promoción del modelo es externa al servicio
status: stable
last-verified: 2026-05-19
owners: [analytics-service]
related: [[analytics-service]], [[avm-training]], [[adr-training-separated-from-runtime]]
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
decision-date: 2026-05-19
decision-status: accepted
---

# ADR-0003 — Promoción del modelo es externa al servicio

## Contexto

Cuando hay una nueva versión del modelo entrenada y registrada en MLflow:
- ¿Quién decide cuándo empieza a servir requests?
- Si es automático: ¿qué criterio aplica (test MAE < umbral, % mejora vs current)?
- Si es manual: ¿quién aprueba y cómo se audita?

El servicio `analytics-service` necesita saber qué versión servir en cada momento.

## Decisión

La promoción a `production` (setear el alias del MLflow registry) es **manual y responsabilidad del data team**. El servicio `analytics-service` **no tiene gate** de aprobación, comparación, ni lógica de validación. Simplemente lee del alias `production` lo que esté ahí en cada `get_version()` call.

El servicio queda **agnóstico al criterio de promoción** — el data team puede cambiar su criterio (cron, drift detection, comparación de métricas, sign-off manual) sin tocar código del servicio.

## Alternativas consideradas

- **Auto-promote basado en métricas** — si el nuevo modelo bate al actual en RMSE/MAPE, se promueve automáticamente. Riesgo: drift insidioso, sin humano en el loop, métricas pueden engañar (Goodhart).
- **Gate en analytics-service** — el servicio compara test set local antes de aceptar el modelo nuevo. Acopla lógica de validación al runtime; el runtime tendría que mantener un test set actualizado.
- **Promotion via CI** — un job de CI valida el modelo y mueve el alias. Requiere pipeline configurado y mantenido; añadir esto puede venir en una iteración futura sin invalidar este ADR.

## Consecuencias

- ✅ Frontera clara entre equipos: data decide qué modelo, runtime lo sirve.
- ✅ `analytics-service` queda 100% agnóstico al criterio de promoción.
- ✅ Trazabilidad: cada cambio de alias queda registrado en MLflow.
- ✅ Permite criterios de promoción complejos (offline experiments, A/B, sign-off ético) sin acoplar al runtime.
- ❌ Sin gate automatizado: se puede promover un modelo peor por error humano.
- ❌ Hoy no hay registro de QUIÉN promovió ni POR QUÉ — depende del rigor del data team y de los comments en MLflow.
- ❌ Riesgo operativo: si nadie promueve cuando se necesita, el servicio sirve un modelo viejo silenciosamente.

## Claims

- `AVMModelAdapter` hardcodea `alias="production"` y lee siempre lo que ese alias apunte ([avm_model_adapter.py:10](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L10)).
- El pipeline de training NO setea el alias — termina con `mlflow.pyfunc.log_model(...)` pero no llama `set_registered_model_alias` ([trainer.py:117-133](data/ml/AVM/training/pipeline/trainer.py#L117-L133)).
- El servicio consulta `client.get_version(model_name, alias)` en cada predicción para obtener el `model_version` que se persiste con la predicción ([avm_model_adapter.py:10-12](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L10-L12)) — útil para auditoría aunque el modelo cargado en memoria no cambie hasta el próximo `ModelClient.__init__` (restart).
