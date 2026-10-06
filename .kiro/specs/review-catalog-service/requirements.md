# Revisión de catalog-service — requisitos

## Objetivo
Encontrar bugs de lógica, mejoras y desvíos de convenciones en `backend/catalog-service`, sin modificar código. Seguir #review.

## Requisitos

1. CUANDO la revisión empiece, EL agente DEBE leer `audit-report.txt` y tratar cada test rojo o error de lint como pista.
2. EL agente DEBE revisar por rebanadas verticales (ruta → caso de uso → repositorio/SQL → schema), en el orden de `tasks.md`.
3. CUANDO una rebanada viole una regla de `domain-invariants.md`, EL agente DEBE reportarla como **Bug** con escenario de falla.
4. SI un posible bug no tiene un escenario de falla concreto, EL agente DEBE reportarlo como **Mejora** con confianza baja, o descartarlo.
5. EL agente NO DEBE reportar ítems que ya estén en `docs/wiki/_shared/open-items.md`, salvo que encuentre información nueva.
6. EL agente NO DEBE editar archivos ni ejecutar comandos que escriban.
7. EL reporte DEBE seguir el formato de #review e incluir la sección "Revisado sin hallazgos".
