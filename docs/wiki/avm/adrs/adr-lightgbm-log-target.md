---
title: ADR-0001 — LightGBM con target log10 y categóricas nativas
status: stable
last-verified: 2026-07-15
owners: [data]
related:
  - "[[avm-training]]"
  - "[[analytics-service-prediction]]"
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0001 — LightGBM con target log10 y categóricas nativas

## Contexto

El AVM predice el precio de venta de inmuebles en Bogotá. Los precios son fuertemente sesgados a la derecha (cola larga de propiedades caras) y abarcan varios órdenes de magnitud. Las features incluyen variables categóricas de alta cardinalidad (barrio, celdas H3) además de numéricas. Hay que elegir el algoritmo y cómo tratar el target y las categóricas.

## Decisión

- **Algoritmo: LightGBM** (gradient boosting sobre árboles) como regresor.
- **Target transformado: `log10(price)`** — se entrena sobre el log y en inferencia se revierte con `10 ** booster.predict(...)`.
- **Categóricas nativas**: las columnas categóricas se castean al dtype `category` de pandas y LightGBM las consume directamente — **sin one-hot encoding**.
- **Métricas en dos escalas**: RMSE en escala log (lo que optimiza el modelo) y MAPE en escala $ COP real (lo interpretable para negocio).

## Alternativas consideradas

- **Regresión lineal / ElasticNet** — interpretable pero no captura las interacciones no lineales (precio × barrio × área) que dominan el avalúo inmobiliario.
- **Redes neuronales** — potentes, pero requieren más datos y tuning, y son menos interpretables; overkill para ~53k propiedades tabulares.
- **XGBoost / CatBoost** — comparables a LightGBM; `catboost` está incluso en las dependencies, pero el pipeline usa LightGBM (más rápido en entrenamiento y soporte nativo de categóricas maduro).
- **Target sin transformar (`price`)** — el sesgo y la heterocedasticidad inflan el error en las propiedades caras; el log estabiliza la varianza.
- **One-hot de categóricas** — explota la dimensionalidad con barrios/H3 de alta cardinalidad; las categóricas nativas de LightGBM lo evitan.

## Consecuencias

- ✅ Captura no linealidades e interacciones sin feature engineering manual de cruces.
- ✅ El target log estabiliza la varianza y mejora el ajuste en la cola de precios.
- ✅ Categóricas nativas → sin explosión dimensional, entrenamiento más rápido, splits que respetan la cardinalidad.
- ✅ Doble métrica (log RMSE + $ MAPE) cubre optimización e interpretabilidad de negocio.
- ❌ El target log sesga el error: minimizar RMSE en log no es lo mismo que minimizar error relativo en $; hay que mirar el MAPE para la lectura real.
- ❌ LightGBM con categóricas de muy alta cardinalidad (H3 r8) puede sobreajustar splits raros — mitigado por regularización en la HPO.
- ❌ Menos interpretable que un lineal — requiere SHAP/feature importance para explicar avalúos.

## Claims

- El target es `log10(price)`, revertido en inferencia con `10 ** booster.predict(...)` ([data.py:22](data/ml/AVM/training/pipeline/data.py#L22), [avm_model.py:6](data/ml/AVM/training/avm_model.py)).
- LightGBM consume las categóricas nativamente vía `cast_categoricals`, sin one-hot ([encoders.py:51-54](data/ml/AVM/training/transforms/encoders.py#L51-L54)).
- Se evalúa con RMSE en escala log y MAPE en escala $ COP ([trainer.py](data/ml/AVM/training/pipeline/trainer.py)).
- `catboost` está en las dependencies pero el pipeline usa solo LightGBM ([pyproject.toml](data/ml/AVM/pyproject.toml)).
