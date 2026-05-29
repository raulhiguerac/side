---
title: ADR-0003 — Precio estimado dual (admin vs ML) en columnas separadas
status: stable
last-verified: 2026-05-28
owners: [properties-service]
related: [[properties-service-admin]], [[analytics-service]], [[avm-training]]
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0003 — Precio estimado dual (admin vs ML) en columnas separadas

## Contexto

Una propiedad puede tener un precio estimado por dos fuentes distintas: un **admin** (avalúo manual/curado) y el **modelo AVM** ([[analytics-service]], [[avm-training]]). Ambas señales tienen valor: el avalúo manual es ground-truth curado útil como label de training; la predicción ML es la salida del modelo que se quiere medir contra ese ground-truth. La pregunta: ¿se guardan en una sola columna (la última gana) o por separado?

## Decisión

- **Dos columnas separadas** en `properties`: `admin_estimated_price` (+ `admin_estimated_price_at`) y `ml_estimated_price` (+ `ml_estimated_price_at`). Ninguna pisa a la otra.
- **Un solo use case** (`SetEstimatedPriceUseCase`) decide a cuál escribir según el actor:
  - **con `principal`** → es un admin → escribe `admin_estimated_price` + timestamp + `updated_by`.
  - **sin `principal`** → es el path ML → escribe `ml_estimated_price` + timestamp.
- **Ninguno de los dos se expone** en `PropertyDetailSchema` — son señales internas, no datos de cara al usuario.

## Alternativas consideradas

- **Una sola columna `estimated_price`** — pierde una de las dos señales; imposible comparar predicción vs avalúo curado para evaluar el modelo.
- **Tabla de histórico de estimaciones** (append-only, con source y timestamp) — más rico para auditoría/series temporales, pero overkill para MVP; se puede migrar a esto después sin romper el contrato.
- **Dos use cases distintos** (uno admin, uno ML) — más explícito, pero duplica la lógica de fetch/commit; el branch por `principal` es trivial y mantiene un solo punto de escritura.

## Consecuencias

- ✅ Ambas señales coexisten — el AVM puede entrenarse contra el avalúo admin y evaluarse contra su propia predicción histórica.
- ✅ Auditoría básica: cada columna lleva su `_at`; la admin además `updated_by`.
- ✅ Un único UC, sin duplicación.
- ❌ **El path ML no tiene caller al 2026-05-28** — `workers/` está vacío; nadie invoca el UC sin principal. La columna `ml_estimated_price` solo se puede poblar manualmente hoy. El consumidor natural es un worker que escuche `price-predicted` de analytics (pendiente).
- ❌ Solo se guarda el **último** valor por fuente, no histórico — si se quiere serie temporal de estimaciones hay que migrar a tabla aparte.
- ❌ El branch por `principal is None` es implícito: un futuro caller que olvide pasar principal escribiría en la columna ML sin querer.

## Claims

- `properties` tiene 4 columnas para estimaciones: `admin_estimated_price`/`_at` y `ml_estimated_price`/`_at` ([property.py:162-173](backend/properties-service/src/app/models/property.py#L162-L173)).
- `SetEstimatedPriceUseCase` escribe la columna admin si hay `principal`, la ML si no ([set_estimated_price.py:26-32](backend/properties-service/src/app/services/admin/use_cases/estimated_price/set_estimated_price.py#L26-L32)).
- Ni `admin_estimated_price` ni `ml_estimated_price` aparecen en `PropertyDetailSchema` ([property_detail.py:40-70](backend/properties-service/src/app/services/shared/schemas/property_detail.py#L40-L70)).
- El path ML (principal=None) no tiene caller — `workers/` está vacío al 2026-05-28 ([workers/](backend/properties-service/src/app/workers)).
