# Revisión de analytics-service — tareas

- [ ] 1. Leer `audit-report.txt` (analytics-service) y los pendientes de analytics en `open-items.md`.
- [ ] 2. Consumer `listing_created`: commit de offsets frente a éxito del procesamiento, mensajes inválidos, reintentos, idempotencia, qué hace si MLflow o la DB no responden.
- [ ] 3. Carga del modelo (`models:/…@production`): cuándo se carga, qué pasa si falla al arrancar, recarga, cache.
- [ ] 4. `POST /predict`: validación de features contra el schema, valores fuera de rango, coherencia con las features del training, errores del modelo.
- [ ] 5. Dominio `market`: consultas, agregaciones y bordes (sin datos, un solo dato).
- [ ] 6. Transversal: auth, CORS, settings con valores fijos.
- [ ] 7. Tests y reporte con el formato de #review.
