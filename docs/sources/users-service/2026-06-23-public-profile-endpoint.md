---
title: Endpoint público de perfil por account_id
captured-from: conversation
captured-on: 2026-06-23
participants: [raul, claude]
---

## Context

users-service solo exponía perfil vía `/me/profile`, atado siempre a `principal.sub` del JWT. El front necesita una página pública de perfil del publicante (`PublicProfileView.vue`, ver `properties-service` open-items) que cualquier visitante anónimo pueda ver — requería un endpoint nuevo sin auth, recibiendo el `account_id` de otro usuario.

## Key conclusions

- El refactor fue mínimo porque `ProfileApplicationService` (`get_profile_orchestrator.py`) ya separaba `get_profile()` (sin chequeo de cuenta activa) de `get_active_profile()` (requiere cuenta activa) — pensado originalmente para reactivación/admin, no para vista pública.
- **Decisión explícita**: el endpoint público usa `get_active_profile()`, no `get_profile()`, aunque el docstring viejo de `get_profile()` mencionaba "public views" como caso de uso. Razón: una cuenta desactivada no debe ser visible a nadie, ni siquiera en modo "vista pública" — mismo comportamiento que ya tiene `/me/profile` para uno mismo. El docstring se corrigió para reflejar esto.
- Nuevo: `GetProfileByIdUseCase.execute(*, account_id)` → `profile_service.get_active_profile(account_id=account_id)`. Dep `get_profile_by_id_uc` reusa el mismo `get_profile_application()` ya wireado. Ruta `GET /v1/users/profiles/{account_id}`, sin `Depends(get_current_principal)`.
- **Cache ya funcionaba gratis**: `profile_cache_key(account_id)` ya estaba parametrizada por `account_id` puro (no por "current user"), así que el endpoint nuevo cae en la misma cache key que ya se llena cuando ese usuario consulta su propio `/me/profile`. Cero cache nueva necesaria.
- Gap conocido y aceptado: en cache-hit, `_get_profile` devuelve el perfil cacheado sin volver a chequear `is_active` — si una cuenta se desactiva durante el TTL de cache (`PROFILE_CACHE_TTL_SECONDS=600`), el perfil público puede seguir visible hasta por 10 minutos. No se resolvió, queda como deuda conocida.
- `created_at` para "miembro desde X" en el front: se decidió **no** threadearlo desde `Account.created_at` vía el orchestrator (cambio de firma en 3 archivos) — en su lugar, `UserProfile`/`CompanyProfile` ya tienen su propio `created_at` (mismo patrón audit), disponible directo en `profile_db` dentro de `CurrentProfileReader.get()`. Fix real: 2 archivos (`schemas/current.py` agrega el campo a `CurrentUserPerson`/`CurrentUserOrganization`; `helpers/mapper.py` lo pasa desde `profile_db.created_at`). Mucho menos invasivo que la primera implementación intentada.
- `created_at` quedó **fuera** de `CurrentUserOut` (el DTO de `/me`, privado) — ese endpoint no lo necesita y no es el que consume la vista pública.

## Open questions

- Ninguna abierta sobre el endpoint en sí; el gap de cache-hit + cuenta desactivada queda como decisión consciente de no resolver ahora.

## Next steps

- Front: armar composable de cards paginadas (offset/limit, no cursor-stack como `useFeed`, porque el listado de un perfil es invertible) — pendiente, el dev lo va a implementar en modo aprendizaje.
- Wiki: agregar evento `account.deactivated` → consumer en properties-service para marcar listings `inactive` (ya está como ítem en `open-items.md`, sin implementar).
