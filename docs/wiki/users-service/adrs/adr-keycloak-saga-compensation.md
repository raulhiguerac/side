---
title: ADR-0001 — Registro como saga con compensación de Keycloak
status: stable
last-verified: 2026-05-28
owners: [users-service]
related: [[users-service-auth]], [[users-service-keycloak]], [[users-service-kc-compensation]]
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0001 — Registro como saga con compensación de Keycloak

## Contexto

Registrar una cuenta toca dos sistemas que **no comparten transacción**: Keycloak (credenciales, fuente de verdad de identidad) y la DB local (`accounts` + perfil, metadata de negocio). El usuario de Keycloak debe crearse antes para obtener el UUID que usamos como `account_id`. Si la escritura en DB falla después, queda un usuario fantasma en Keycloak sin cuenta local — un estado inconsistente que además bloquea el email (que es único).

## Decisión

- **Orden fijo**: crear en Keycloak primero (obtener UUID) → escribir `Account` + perfil en DB → commit. El `account_id` local **es** el UUID de Keycloak (identidad compartida, sin tabla de mapeo).
- **Compensación inline**: si la DB falla, hacer rollback y borrar el usuario recién creado en Keycloak.
- **Compensación diferida**: si ese borrado inline también falla (IdP caído/timeout), **encolar un `KcCompensationTask`** en la tabla local para reintento async.
- **Worker de reintento**: un job periódico ([[users-service-kc-compensation]]) procesa la cola con backoff exponencial y un tope de intentos.
- **Guard de email**: chequear disponibilidad del email antes de tocar Keycloak, para fallar barato en el caso común de duplicado.

## Alternativas consideradas

- **DB primero, Keycloak después** — no funciona: necesitamos el UUID de Keycloak como PK antes de escribir el `Account`.
- **Two-phase commit / transacción distribuida** — Keycloak no lo soporta; complejidad enorme para el volumen actual.
- **Solo compensación inline (sin cola)** — si el IdP está caído justo cuando falla la DB, el usuario fantasma queda para siempre. La cola da consistencia eventual.
- **Outbox/event-driven** — más robusto y desacoplado, pero requiere infra de mensajería que el servicio no tiene hoy; la cola en tabla + scheduler es el mínimo viable.

## Consecuencias

- ✅ Nunca queda (de forma permanente) un usuario en Keycloak sin `Account` local.
- ✅ Identidad compartida (UUID = sub = account_id) simplifica todos los joins lógicos con el IdP.
- ✅ Fail-fast barato en el caso común (email duplicado) antes de tocar Keycloak.
- ✅ Resiliente a caídas transitorias del IdP gracias a la cola + reintentos.
- ❌ **Ventana de inconsistencia** entre el fallo y el reintento exitoso: existe un usuario huérfano en Keycloak hasta que el worker lo borra (hasta minutos/horas según backoff).
- ❌ Una task que agota `MAX_ATTEMPTS` queda en `failed` y requiere intervención manual.
- ❌ La cola + scheduler es lógica custom a mantener; un outbox/mensajería sería más estándar a mayor escala.

## Claims

- El registro crea el usuario en Keycloak y usa su UUID como `account_id` ([register_account.py:77-85](backend/users-service/src/app/services/auth/use_cases/register_account.py#L77-L85)).
- Ante fallo de DB se intenta borrar el usuario de Keycloak; si falla, se encola un `KcCompensationTask` ([register_account.py:40-58](backend/users-service/src/app/services/auth/use_cases/register_account.py#L40-L58), [register_account.py:98-138](backend/users-service/src/app/services/auth/use_cases/register_account.py#L98-L138)).
- El email se valida con `AccountEmailAvailabilityPolicy` antes de tocar Keycloak ([register_account.py:67](backend/users-service/src/app/services/auth/use_cases/register_account.py#L67)).
- La cola es la tabla `kc_compensation_tasks` con `status`/`attempts`/`next_retry_at` ([kc_tasks.py:20-35](backend/users-service/src/app/models/kc_tasks.py#L20-L35)).
