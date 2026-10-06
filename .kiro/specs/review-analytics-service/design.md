# Revisión de analytics-service — diseño

Dominios `prediction` (AVM online en `POST /predict`, modelo desde el registro de MLflow) y `market`, más el consumer de Kafka `listing_created` que predice en lote. El training vive en `data/ml/` y queda fuera.

Contexto: #[[file:docs/wiki/analytics-service/analytics-service.md]]

Orden: primero el consumer (corre sin supervisión y puede perder o duplicar mensajes), después la carga del modelo y `/predict`.
