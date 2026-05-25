---
title: ADR-0001 — Auth vía Keycloak JWT
status: stable
last-verified: 2026-05-20
owners: [_shared]
related: [[architecture]], [[analytics-service-architecture]]
sources: [../../../sources/analytics-service/2026-05-19-foundational-qa.md, ../../../sources/analytics-service/2026-05-20-prediction-wiring-and-batch-uc.md]
decision-date: 2026-05-19
decision-status: accepted
---

# ADR-0001 — Auth vía Keycloak JWT

## Contexto

Sistema distribuido con múltiples microservicios. Cada uno necesita identificar al actor de cada request (usuario o sistema). Sin una solución central, cada servicio termina implementando su propia auth — duplicación + drift + brecha de seguridad. Restricciones: stack cloud-agnostic, sin créditos en ninguna nube.

## Decisión

**Keycloak self-hosted** como Identity Provider único del sistema. `users-service` actúa como gateway/wrapper de Keycloak para el resto del backend. Cada microservicio backend tiene una FastAPI dependency en `api/deps/` que valida el JWT del header `Authorization` y entrega un `principal: uuid.UUID` al UC. **Los UCs nunca ven el token** — operan sobre el UUID resuelto.

Para flujos server-to-server (consumer async de analytics), el `principal` es un **system ID fijo** del servicio que emite el mensaje (no el usuario real).

## Alternativas consideradas

- **Auth0 / AWS Cognito / Firebase Auth** — managed pero requieren créditos cloud y atan al proveedor. Descartado por la restricción cloud-agnostic.
- **JWT propio + librería custom** — más control pero requiere mantener crypto, rotación de keys, UI de admin de usuarios. Reinventar la rueda.
- **OAuth2 directo sin Keycloak** — más manual, sin UI de admin out-of-the-box.

## Consecuencias

- ✅ Una única fuente de verdad para identidad.
- ✅ Stack 100% portable, corre en cualquier docker host.
- ✅ Los UCs nunca tocan crypto ni hablan con Keycloak — separación limpia, fácil de testear.
- ✅ Keycloak ya tiene admin UI, roles, federación, theming.
- ❌ Hay que operar Keycloak (DB propia, upgrades, scaling, backups).
- ❌ Latencia adicional en validación del token vs JWT verificado localmente con public key — mitigable cacheando la public key.

## Claims

- Cada microservicio backend tiene un `api/deps/` que resuelve el JWT a un `principal`.
- Los UCs reciben `principal: uuid.UUID`, nunca el token.
- En `analytics-service`, la dependency existe desde 2026-05-20 en `api/deps/auth.py` (`get_current_principal`). Lee la cookie `access_token`, valida JWT vía `PyJWKClient`, retorna `Principal`. Errores en `core/exceptions/auth.py` (no en el dep).
- `api/deps/__init__.py` está vacío — cada responsabilidad en su propio archivo (`auth.py`, `db.py`, `prediction.py`).
