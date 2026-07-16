---
title: ADR-0002 — HPO con Optuna y reproducibilidad por seeds fijas
status: stable
last-verified: 2026-07-15
owners: [data]
related:
  - "[[avm-training]]"
  - "[[adr-lightgbm-log-target]]"
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0002 — HPO con Optuna y reproducibilidad por seeds fijas

## Contexto

LightGBM tiene muchos hiperparámetros que interactúan (profundidad, hojas, learning rate, regularización, sampling). Una búsqueda manual es lenta y poco reproducible. Además, el pipeline se corre a mano hoy, así que dos corridas con los mismos datos deberían dar el mismo modelo para poder comparar versiones de forma justa.

## Decisión

- **Optuna con `TPESampler` (Tree-structured Parzen Estimator)**, 400 trials, minimizando RMSE en el val set.
- **Seeds fijas en todo**: `random_state=42` en el split, `TPESampler(seed=42)`, y seeds en LightGBM — para reproducibilidad bit-a-bit.
- **Split estratificado 70/15/15** por `tipo_propiedad` (apartment/house), para que train/val/test mantengan la proporción de tipos.
- **Refit en dos fases**: con los `best_params` de Optuna, (1) re-entrena en train con early stopping en val para hallar `best_rounds`, luego (2) **re-entrena en train+val combinados** con esos rounds → modelo final. El test queda intacto para la métrica reportada.
- **HPO trazable en MLflow**: el tuning se loguea bajo un run `optuna_fine_tuning` separado del `final_model`.

## Alternativas consideradas

- **Grid search** — explota combinatoriamente; ineficiente para 9 hiperparámetros continuos.
- **Random search** — mejor que grid, pero TPE converge más rápido al explotar trials previos.
- **Sin refit en train+val** — desperdicia el val set en el modelo final; combinarlo aprovecha más datos sin tocar el test.
- **Seeds aleatorias** — impide comparar versiones de forma justa y dificulta debugging; las seeds fijas priorizan reproducibilidad sobre estimar varianza entre corridas.

## Consecuencias

- ✅ Búsqueda eficiente (TPE aprovecha la historia de trials).
- ✅ Reproducible: misma data + mismo código → mismo modelo, comparaciones de versión justas.
- ✅ El refit train+val exprime los datos disponibles sin filtrar el test.
- ✅ HPO auditable en MLflow (run separado).
- ❌ Seeds fijas **ocultan la varianza** entre corridas — un modelo "mejor" podría serlo por suerte de seed; no se mide el intervalo de confianza.
- ❌ 400 trials × LightGBM es caro en tiempo de cómputo para correr a mano sin orchestrator.
- ❌ Optimizar RMSE en log (no MAPE en $) puede no alinear perfectamente con el objetivo de negocio (ver [[adr-lightgbm-log-target]]).
- ❌ El número de trials (400) es un número fijo, no un criterio de parada por convergencia — puede sobrar o faltar según el caso.

## Claims

- Optuna corre 400 trials con `TPESampler` minimizando RMSE en val ([tuner.py:62](data/ml/AVM/training/pipeline/tuner.py#L62)).
- El split es 70/15/15 estratificado por `tipo_propiedad` con `random_state=42` ([train.py:23-29](data/ml/AVM/training/train.py#L23-L29)).
- El modelo final re-entrena en train+val con los `best_rounds` de early stopping en val ([trainer.py:68-93](data/ml/AVM/training/pipeline/trainer.py#L68-L93)).
- El tuning se loguea en MLflow bajo un run `optuna_fine_tuning` separado del `final_model` ([tuner.py](data/ml/AVM/training/pipeline/tuner.py)).
- Las seeds están fijas (split, sampler, LightGBM) para reproducibilidad ([train.py](data/ml/AVM/training/train.py), [tuner.py](data/ml/AVM/training/pipeline/tuner.py)).
