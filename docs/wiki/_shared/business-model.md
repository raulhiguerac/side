---
title: Modelo de negocio y monetización
status: draft
last-verified: 2026-06-25
owners: [_shared]
related:
  - "[[properties-service-search]]"
  - "[[properties-service-admin]]"
  - "[[adr-feed-ads-organic-injection]]"
  - "[[project-roadmap-2026]]"
  - "[[glossary]]"
sources: []
---

## TL;DR

Plataforma PropTech all-in-one para el mercado colombiano. El diferenciador frente a portales tradicionales es la integración de marketplace + ML de precios + matching/roommates + B2B data + FinTech en una sola experiencia. La monetización arranca con listings promocionados (ya implementados) y comisiones, y escala hacia data analytics y FinTech.

## Fuentes de monetización por fase

### MVP / Fase 2 — implementadas o próximas

- **Listings promocionados**: `is_promoted` + `promoted_until` en la tabla de propiedades. El feed intercala ads 1 cada `FEED_AD_INTERVAL=5` posiciones orgánicas. El admin crea/borra promociones vía `CreatePromotionUseCase` / `DeletePromotionUseCase`. Paquetes por duración (1 semana, 1 mes). Ver [[properties-service-admin]] y [[adr-feed-ads-organic-injection]].
- **Comisión por arriendo**: cuando la plataforma facilita el cierre → % mensual del arriendo.
- **Comisión por venta**: como broker (comisión compartida con inmobiliarias, comisión completa con usuarios directos).

### Fase 3 — B2B data

- **Data analytics B2B**: precio/m², tendencias por barrio, tiempos de mercado, popularidad de zonas — vendidos a agentes, inmobiliarias, bancos. Requiere DWH con snapshots diarios (BigQuery o DuckDB sobre MinIO).
- **Reportes premium**: pago por informe o suscripción — valoración ML, detección de oportunidades de inversión.
- **Alertas premium**: "propiedad 20% bajo precio esperado en tu zona".

### Fase 4 — Social + inversión

- **Matching/roommates**: usuarios con intereses similares conectados → lead calificado al propietario → comisión por cierre. Competidor directo: Rentpana (solo ese nicho, sin marketplace).
- **Panel de inversores**: score de oportunidad, ROI estimado, alertas exclusivas → suscripción mensual/anual.

### Largo plazo — FinTech

- Simulador de crédito hipotecario (gratis, fidelización).
- Leads a brokers/bancos → comisión por cierre o lead calificado.
- Precalificación automática con datos del marketplace.
- Crédito directo para flipping (requiere regulación Superfinanciera Colombia).

## ML de precios (AVM)

- **Dataset**: ~180k registros con features (lat/lon, m², tipo, hab, baños, barrio, precio).
- **Approach**: KNN Regressor con Ball-Tree — filtro previo por neighborhood + radio 2km (Haversine/PostGIS).
- **Output**: `estimated_price` en la propiedad al publicar; badge 🟢/🟡/🔴 en feed según score `(precio_listado - precio_estimado) / precio_estimado`.
- **Enriquecimiento**: POIs de Overpass (ya integrada en catalog-ms) como features de amenities cercanas.
- El endpoint `/v1/predict` ya está operativo (analytics-ms). Ver [[analytics-service-prediction]].

## Análisis competitivo

| Competidor | Fuerte en | Débil en | Relación |
|---|---|---|---|
| **Cerouno** (Medellín→Bogotá) | Búsqueda NLP, isocronas, calculadora de inversión, SEO | Matching, ciclo completo, B2B, FinTech | Posible aliado/adquisición — complementarios |
| **Rentpana** (Bogotá+Medellín) | Matching roommates verificados, jóvenes profesionales, 4.8/5 | Solo ese nicho, sin marketplace general, sin ML | Competidor directo en matching; ventaja propia: marketplace completo + onboarding con intent/ciudad/barrio |
| **Habi** | Compraventa directa (iBuyer), brand reconocida | Arriendo, matching, B2B data | Competidor indirecto |
| **Metrocuadrado / FincaRaíz** | Volumen de listings | Sin ML, sin matching, sin analytics propios, UX desactualizada | Competidores directos en marketplace |

## El moat

La integración del ciclo completo: **buscar → evaluar (ML) → conectar (matching) → financiar (FinTech)**. Ningún competidor en Colombia tiene todo esto junto.

El modelo de datos ya captura desde Fase 2 lo que necesita Fase 4: `intent`, `presupuesto`, `neighborhood_interest` en el onboarding de `users-service`.

## Features planeadas

- **Búsqueda con lenguaje natural**: LLM con tool use para traducir input del usuario → parámetros de `GET /v1/search/feed` (preferences + filters). Similar a Cerouno, pero dentro de un marketplace completo.

## Claims

- `is_promoted` en `PropertyCardSchema` se deriva de la presencia de una promoción activa en `Property.promotions` (relación viewonly filtrada por `is_active=True`) ([property_card.py:64-69](backend/properties-service/src/app/services/shared/schemas/property_card.py#L64-L69)).
- El feed intercala 1 ad cada `FEED_AD_INTERVAL=5` posiciones orgánicas; el máximo de ads por página es `min(len(ads), page_size // 5)` ([get_feed.py:32-33](backend/properties-service/src/app/services/search/use_cases/get_feed.py#L32-L33)).
- payments-ms está en fase draft — no hay código en el repo ([project-roadmap-2026](wiki/_shared/project-roadmap-2026.md)).
- El stack de pagos no está decidido: Stripe (USD) vs Wompi/PSE (COP) ([project-roadmap-2026](wiki/_shared/project-roadmap-2026.md)).
