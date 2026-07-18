---
title: ADR-0004 — Deactivación soft (Keycloak retiene el usuario)
status: stable
last-verified: 2026-07-15
owners: [users-service]
related:
  - "[[users-service-user]]"
  - "[[users-service-keycloak]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0004 — Deactivación soft (Keycloak retiene el usuario)

## Contexto

Un usuario puede querer "borrar" su cuenta. Eliminar duro implicaría borrar el `Account` local, el perfil, los intereses y el usuario de Keycloak — irreversible y costoso si el usuario se arrepiente. Además, el `account_id` es la identidad referenciada por otros servicios (p. ej. `owner_id` de listings en [[properties-service]]); un hard-delete dejaría referencias colgando.

## Decisión

- **Deactivación soft**: marcar `accounts.is_active=False` + metadata (`deactivated_at`, `deactivated_by`, `deactivation_reason`). No se borran filas.
- **Keycloak retiene el usuario** — a diferencia del rollback de registro, la deactivación **no** llama a `delete_account` en el IdP. El usuario queda pero el login efectivo se corta a nivel de negocio (las lecturas exigen `is_active`).
- **Reactivación por email**: `request` manda un token (mismo patrón one-shot que reset), `confirm` vuelve `is_active=True`.
- **Logout best-effort** al deactivar: se revoca la sesión pero un fallo de logout nunca bloquea la deactivación.
- **Lecturas conscientes del estado**: el orquestador de perfil distingue `get_profile` (permite inactivas: reactivación/admin) de `get_active_profile` (solo activas).

## Alternativas consideradas

- **Hard delete** (DB + Keycloak) — cumple "derecho al olvido" literalmente, pero irreversible, rompe FKs cross-service, y borra datos potencialmente necesarios para auditoría/legal. Se puede ofrecer como flujo aparte si lo exige compliance.
- **Deshabilitar el usuario en Keycloak** (`enabled=false`) además del flag local — defensa en profundidad (Keycloak rechazaría el login directamente), pero hoy se confía en el flag local; queda como mejora.
- **Anonimización** (borrar PII, conservar la fila) — buen punto medio para compliance, pero más trabajo; no se hizo en MVP.

## Consecuencias

- ✅ Reversible: reactivar es un flip de flag, sin recrear identidad ni perder datos.
- ✅ No rompe referencias cross-service al `account_id`.
- ✅ Conserva historial para auditoría (quién/cuándo/por qué se deactivó).
- ✅ La reactivación reusa el mecanismo de action tokens ya existente.
- ❌ **El usuario sigue existiendo en Keycloak y habilitado** — si algún flujo no chequea `is_active`, podría autenticar. La defensa es a nivel de negocio, no de IdP.
- ❌ **No satisface "borrado real"** para compliance estricto (GDPR/Habeas Data) — falta un flujo de hard-delete/anonimización.
- ❌ Cuentas soft-deactivated **se acumulan** indefinidamente — no hay limpieza ni `system_cleanup` automatizado hoy (el enum lo contempla, pero nadie lo dispara).

## Claims

- La deactivación setea `is_active=False` + `deactivated_at/by/reason`, sin borrar filas ([deactivate_current_account.py:27-30](backend/users-service/src/app/services/user/use_cases/account/deactivate_current_account.py#L27-L30)).
- La deactivación **no** borra el usuario de Keycloak (solo el rollback de registro lo hace) ([deactivate_current_account.py:20-42](backend/users-service/src/app/services/user/use_cases/account/deactivate_current_account.py#L20-L42)).
- El endpoint hace un logout best-effort que nunca bloquea la deactivación ([user.py:177-183](backend/users-service/src/app/api/routes/user.py#L177-L183)).
- El orquestador distingue `get_profile` (inactivas) de `get_active_profile` (solo activas) ([get_profile_orchestrator.py:24-53](backend/users-service/src/app/services/user/services/get_profile_orchestrator.py#L24-L53)).
- El enum `AccountDeactivationReason` incluye `system_cleanup`, pero no hay job que lo use al 2026-05-28 ([account.py:21-28](backend/users-service/src/app/models/account.py#L21-L28)).
