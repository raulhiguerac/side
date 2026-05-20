---
title: Foundational Q&A — analytics-service
captured-from: conversation
captured-on: 2026-05-19
participants: [author, claude]
---

## Context

Primera sesión de captura del wiki piloto (Día 2-3 del plan). Cubrió scope, arquitectura, dominio, integraciones y operaciones de `analytics-service` para alimentar las páginas iniciales del wiki.

## Key conclusions

### Scope & boundaries
- analytics-service hospeda dos dominios: `prediction` (AVM) y `market` (insights B2B sobre snapshots periódicos).
- AVM: estimación de precio de **venta** hoy; arriendos a futuro.
- Heatmap (precios y listings) es un job **batch** del dominio market que hace reverse ETL → Redis + DB.

### Consumers de /predict
- **User-driven sincrónico**: hoy solo usuarios registrados (JWT obligatorio). Futuro posible: público con rate limit (~2 calls/IP rolling 2h).
- **Server-to-server vía mensajería**: properties-ms publica `listing creado` en un topic → analytics consume, predice, publica resultado en otro topic → properties actualiza el `estimated_price` del registro. Mecanismo concreto (Kafka o alternativa) **aún en definición**. El scaffolding `src/app/workers/` ya está creado anticipando este flujo.

### Auth
- JWT emitido por **Keycloak** (parte del sistema distribuido alrededor de users-ms).
- Una FastAPI dependency resuelve el token y entrega un UUID `principal` al UC. El UC no ve el token.
- Para el flujo server-to-server, el `principal` será un **system ID** (no el usuario que creó el listing) porque el caso es feedback al modelo, no acción del usuario.

### Stack ML — por qué MLflow + MinIO
- MLflow: estándar de la industria para tracking + monitoreo + model serving amigable.
- MinIO + filosofía cloud-agnostic: sin créditos en ninguna nube por ahora, el ms permite portabilidad.

### Training separation (data/ml/AVM/ fuera del backend)
- Frontera de **equipos**: data team ≠ runtime team. Responsabilidades totalmente aparte.
- MLflow es el **contrato** entre ambos lados. Data experimenta libremente (EDA, experimentos), analytics consume el alias `production`.
- Hoy training manual; futuro pipeline de re-entreno con Airflow u otro.

### Dominio — vocabulario y semántica
- **IDECA**: Infraestructura de Datos Espaciales de Bogotá (https://www.ideca.gov.co/). Estándar oficial para `barrio` normalizado en Bogotá.
- `barrio_ideca` se resuelve **al crear el listing en properties-service** (geocoding desde lat/lon). analytics nunca resuelve geo — lo recibe en el request. Principio: **"geo-enrichment at write time, not read time"**.
- Campo `feedback` (5 niveles muy_mal..muy_bien) en `predictions`: se llenará vía un endpoint futuro de **encuesta de satisfacción post-predicción**. Sesgo de usuario asumido; sirve como métrica de "performance percibido", no de accuracy real.
- POIs para training: hoy CSV de OpenStreetMap manual. `catalog-service` tiene un mecanismo fire-and-forget poblando tabla de POIs; futuro path es DWH, no CSV.

### Operaciones
- **Model promotion**: responsabilidad del **data team** (futuro). Ellos setean el alias `production` en MLflow. analytics-service no decide qué modelo sirve — solo consume el alias. **Sin gate en el servicio**.
- **Redis** se usa para: (a) reverse ETL del heatmap, (b) rate limiting del predict público futuro. **NO** para caché de predicciones.

### Local dev
- `docker-compose.yml` en **root del monorepo** levanta todos los servicios + un **devcontainer**.
- Los servicios corren **dentro del devcontainer** para no contaminar el host.
- Para probar `/predict` local: levantar analytics + obtener token de users-ms.
- Postman collection para el flujo de auth está pendiente (a futuro).

## Open questions

- Mecanismo concreto del consumer server-to-server (Kafka vs alternativa) y nombres de topics.
- Cómo se siembra el modelo en el MinIO local al levantar docker-compose (probable: bucket pre-cargado, o entrenamiento local con subset). Verificar al escribir el runbook leyendo el `docker-compose.yml`.
- Endpoint de feedback de satisfacción: cuándo se construye, qué payload, qué autenticación.
- Timeline para automatizar el training (Airflow u otro).
- Rate limiting del predict público: cuándo se activa, parámetros exactos.

## Next steps

- Construir el primer batch de páginas del wiki en este orden:
  1. `_shared/glossary.md` (IDECA, AVM, principal, alias `production`, POI, devcontainer)
  2. `_shared/architecture.md` (visión monorepo, hex pattern, patrones de comunicación entre servicios)
  3. `analytics-service/00-overview.md`
  4. `analytics-service/architecture.md`
  5. `analytics-service/domain/prediction.md`
  6. `analytics-service/domain/training.md`
- Al llegar a flows/ e integrations/, leer código directamente — no preguntar más.
- Registrar los siguientes ADRs derivados de esta conversación:
  - `_shared/adrs/auth-keycloak-jwt.md`
  - `_shared/adrs/geo-enrichment-at-write-time.md`
  - `analytics-service/adrs/mlflow-minio-stack.md`
  - `analytics-service/adrs/training-separated-from-runtime.md`
  - `analytics-service/adrs/model-promotion-external-to-service.md`
- **NO documentar** `scripts/smoke_online_predict.py` — es provisional, se irá cuando haya tests reales.
