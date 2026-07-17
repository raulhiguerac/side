---
title: JWT role extraction and is_admin on CurrentUserOut
captured-from: conversation
captured-on: 2026-07-16
participants: [raul, claude]
---

## Context
Planning an admin panel (properties/catalog moderation) surfaced that the front cannot read the httpOnly JWT to check the `admin` Keycloak role, so a backend-derived `is_admin` flag was needed on the session bootstrap response. Investigation found `users-service`, unlike `catalog-service`/`properties-service`, never extracted `realm_access.roles` from the token at all.

## Key conclusions
- `Principal` in `users-service` (`app/schemas/common.py`) gained `roles: List[str] = []`; `get_current_principal` (`app/api/deps/auth.py`) now extracts `claims.get("realm_access", {}).get("roles", [])`, mirroring the existing pattern already used in `catalog-service`/`properties-service`.
- Added `ADMIN_ROLE` setting (default `"admin"`) to `users-service`'s `settings.py`, matching the other two services.
- `CurrentUserOut` gained `is_admin: bool = False`. Default is required because `CurrentAccountReader` caches a DB-only `CurrentUserOut` (`model_validate(account)`, no JWT access) — `is_admin` must never be baked into that cache.
- `GetCurrentAccountUseCase.execute()` computes `is_admin` fresh per request, after the cache-aside read: `account.model_copy(update={"is_admin": settings.ADMIN_ROLE in principal.roles})`. Keeps the cached object pure-DB, always re-derives admin status from the current request's JWT.
- Decision: bundle `is_admin` into `GET /v1/users/me/` (`CurrentUserOut`) rather than a dedicated `is-admin`/permission-check endpoint. Matches the common "session bootstrap" pattern (Django `request.user`, Rails `current_user`, NextAuth `session` callback) for a single flat role flag; dedicated permission endpoints are for complex multi-resource authorization matrices (overkill here).
- Important guardrail found: `GET /v1/users/me/profile` (`CurrentUserProfileOut`) must NOT carry `is_admin`. Its orchestrator (`ProfileApplicationService.get_active_profile`) is shared verbatim with the PUBLIC route `GET /v1/users/profiles/{account_id}` (viewing someone else's profile, unauthenticated). Adding `is_admin` there would leak whether an arbitrary third-party account is an admin.

## Open questions
- None on the backend side for this specific plumbing; the admin panel's own endpoints/views are a separate, later effort.

## Next steps
- Frontend consumes `is_admin` via `GET /v1/users/me/` (see the paired `frontend` capture from the same session).
