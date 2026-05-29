---
title: users-service — exploración foundational del código
captured-from: conversation
captured-on: 2026-05-28
participants: [raul, claude]
---

## Context

Primera documentación de `users-service` en la wiki. Se exploró el código a fondo para producir las páginas (overview, arquitectura, dominios, integraciones, worker, runbook, ADRs). Este source registra los hallazgos no triviales.

## Key conclusions

- **Dos dominios** bajo `services/`: `auth` (registro, login/refresh/logout, cambio y reset de password) y `user` (cuenta, perfil, foto, onboarding, intereses, deactivación/reactivación). `shared/` aloja ports/adapters/policies comunes.
- **Es el único servicio que habla con Keycloak para gestionar usuarios** — dos clientes: `KeycloakAdminClient` (crear/borrar usuario, set password; server-to-server con admin secret) y `KeycloakAuthClient` (login/refresh/revoke; OpenID con auth client secret). El resto de servicios solo *valida* JWTs.
- **Registro = saga con compensación**: (1) crear usuario en Keycloak → (2) crear `Account` + perfil en DB → (3) commit. Si la DB falla, se intenta borrar el usuario de Keycloak (compensación inline). Si ese borrado también falla, se **encola un `KcCompensationTask`** en la tabla para reintento async.
- **Worker de compensación corre dentro de FastAPI vía APScheduler** (`core/scheduler.py`, lifespan), cada 900s. Procesa hasta 25 tasks pendientes, backoff exponencial con jitter (cap 60 min), `MAX_ATTEMPTS=5` → status `failed`. **Decisión opuesta** a la del consumer de [[analytics-service]] (proceso separado): acá no hay modelo pesado que mantener en memoria, así que in-process es más simple.
- **Auth de sesión por cookies** (`access_token` + `refresh_token`), seteadas/borradas por `api/http/cookies.py`. Los **action tokens** (confirmar reset password / reactivación) van por **Bearer header**, no cookie.
- **Tokens de un solo uso en Redis**: reset-password y reactivación generan `secrets.token_urlsafe(32)`, guardan en Redis el `account_id` bajo `hash_token(token)` con TTL, y mandan email (Brevo) con URL al frontend. Confirm hace `GETDEL` (consume atómico).
- **Privacidad en flujos por email**: request-reset y request-reactivation devuelven 202 con mensaje genérico aunque la cuenta no exista (no filtran existencia).
- **Deactivación es soft**: `is_active=False` + metadata (`deactivated_at/by/reason`). El usuario de Keycloak **no se borra** (solo se borra en rollback de registro). Reactivación vía token por email.
- **Foto de perfil sube a través del backend** (`UploadFile` → `storage.upload_file`), con validación de MIME/size por dependency — contraste con properties-service que usa presigned URLs (foto única y chica vs muchas imágenes grandes).
- **Onboarding** es una máquina de 4 pasos (`intent → city → neighborhood → property_type → done`) trackeada en `accounts.onboarding_step` + tabla `onboarding_completions`. Los intereses se modelan en `user_interest` / `user_neighborhood_interest` (rank 1-5) / `user_property_type_interest`.
- **API montada bajo `/v1`**; CORS abierto a `localhost:8080` (frontend). El `api_router` **no incluye el health router** (gap menor).
- **6 migraciones Alembic**, **40 tests**. `.env.example` está **completo** (a diferencia de catalog/properties).

## Open questions

- El health router existe (`routes/health.py`) pero no está incluido en `api_router` — ¿intencional?
- ¿Habrá limpieza de cuentas soft-deactivated viejas (system_cleanup) o quedan para siempre?

## Next steps

- Documentar users-service en la wiki (hecho en esta sesión).
- Considerar ADR cross-service del contrato de identidad (quién posee qué entre Keycloak y la tabla `accounts`).
