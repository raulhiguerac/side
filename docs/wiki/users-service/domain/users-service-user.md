---
title: Dominio user — users-service
status: draft
last-verified: 2026-06-23
owners: [users-service]
related:
  - "[[users-service]]"
  - "[[users-service-architecture]]"
  - "[[frontend-onboarding-flow]]"
  - "[[adr-soft-deactivation]]"
  - "[[properties-service-search]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md, ../../../sources/users-service/2026-06-23-public-profile-endpoint.md]
---

## TL;DR

El dominio de **perfil y ciclo de cuenta**: leer/editar el perfil propio, subir foto, completar el onboarding de 4 pasos, registrar intereses, y deactivar/reactivar la cuenta. Las lecturas de perfil usan cache-aside vía un orquestador; la deactivación es soft.

## Use cases

| UC | Archivo | Qué hace |
|---|---|---|
| `GetCurrentAccountUseCase` | `use_cases/account/get_current_account.py` | Datos de cuenta del usuario actual. |
| `GetCurrentProfileUseCase` | `use_cases/profile/get_current_profile.py` | Perfil propio (cache-aside, `principal.sub`). |
| `GetProfileByIdUseCase` | `use_cases/profile/get_profile_by_id.py` | Perfil público de **otra** cuenta, por `account_id` (sin auth). |
| `UpdateCurrentProfileUseCase` | `use_cases/profile/update_current_profile.py` | Patch de perfil; invalida cache. |
| `UpdateCurrentProfilePhotoUseCase` | `use_cases/profile/upload_profile_photo.py` | Sube foto a storage, actualiza `photo_url`/`photo_key`. |
| `GetUserInterestsUseCase` | `use_cases/account/get_interests.py` | Intereses (ciudad/barrio/tipo). |
| `DeactivateCurrentAccountUseCase` | `use_cases/account/deactivate_current_account.py` | Soft-deactivate. |
| `RequestReactivationUseCase` | `use_cases/account/request_account_reactivation.py` | Manda email con token de reactivación. |
| `ConfirmReactivationUseCase` | `use_cases/account/reactivate_current_account.py` | Reactiva con token. |
| `CompleteOnboardingIntentUseCase` | `use_cases/onboarding/complete_intent.py` | Paso 1: intención. |
| `CompleteCityIntentUseCase` | `use_cases/onboarding/complete_interest_city.py` | Paso 2: ciudades. |
| `CompleteNeighborhoodInterestUseCase` | `use_cases/onboarding/complete_interest_neighborhood.py` | Paso 3: barrios rankeados. |
| `CompletePropertyTypeInterestUseCase` | `use_cases/onboarding/complete_interest_property_type.py` | Paso 4: tipo de propiedad. |

## Perfil — persona vs empresa

`accounts.account_type` define si el perfil vive en `user_profile` (persona) o `company_profile` (organización). Los readers (`CurrentProfileReader`, `CurrentAccountReader`) resuelven la tabla correcta según el tipo. El orquestador `ProfileApplicationService` expone `get_profile` (permite cuentas inactivas: reactivación/admin) y `get_active_profile` (solo activas, usado tanto por `/me/profile` como por la vista pública), ambos con cache-aside.

## Perfil público (`GET /v1/users/profiles/{account_id}`)

Endpoint sin auth para que cualquier visitante (anónimo o no) vea el perfil de otra cuenta — pensado para la página pública del publicante de un listing en el frontend. Decisiones de la implementación (2026-06-23):

- **Usa `get_active_profile()`, no `get_profile()`**: aunque el docstring viejo de `get_profile()` mencionaba "public views" como caso de uso, se decidió que una cuenta desactivada no debe ser visible para nadie — ni siquiera en modo público. Mismo gate que ya tiene `/me/profile` para uno mismo.
- **Cero cache nueva**: `profile_cache_key(account_id)` ya estaba parametrizada por `account_id` puro, no por "current user" — el endpoint público cae en la misma key que ya llena el propio `/me/profile` de ese usuario.
- **Gap conocido, sin resolver**: en cache-hit, `_get_profile` devuelve el perfil cacheado sin re-chequear `is_active`. Si una cuenta se desactiva durante el TTL (`PROFILE_CACHE_TTL_SECONDS=600`), el perfil público puede seguir visible hasta 10 minutos después de la desactivación.
- **`created_at` para "miembro desde X" en el front**: viene de `UserProfile.created_at`/`CompanyProfile.created_at` (mismo patrón audit que `Account`), no de `Account.created_at` — evita threadear ese campo a través del orchestrator/reader. `CurrentUserOut` (DTO de `/me`, privado) no lo incluye.

## Foto de perfil

A diferencia de las imágenes de [[properties-service-listing]] (presigned URLs), la foto de perfil **sube a través del backend**: el archivo llega como `UploadFile`, una dependency (`validate_profile_photo_upload`) valida MIME/size, y el UC hace `storage.upload_file` a MinIO con una key determinística por cuenta (`profile_photo_storage_key(account_id)`). Luego actualiza `photo_url`/`photo_key` e invalida la cache de perfil. Es una sola imagen pequeña, así que el costo de proxiar los bytes es aceptable.

## Onboarding — máquina de 4 pasos

`accounts.onboarding_step` avanza `intent → city → neighborhood → property_type → done`. Cada paso completado se registra en `onboarding_completions` (PK `(account_id, key)`). Los intereses se persisten en:

- `user_interest` — una fila por `(account_id, city_id)` (único).
- `user_neighborhood_interest` — barrios con `interest_rank` 1-5 dentro de un interés de ciudad.
- `user_property_type_interest` — tipo (`house`/`apartment`) por interés de ciudad.

Estos intereses alimentan las `FeedPreferences` del feed de [[properties-service-search]]. Ver el lado cliente en [[frontend-onboarding-flow]].

## Deactivación / reactivación

- **Deactivate** (`/users/me/deactivate`): soft — `is_active=False` + `deactivated_at/by/reason` (`user_request`). El usuario de Keycloak **no se borra**. Invalida cache de cuenta/perfil. El endpoint hace además un logout best-effort. Ver [[adr-soft-deactivation]].
- **Reactivation request** (`/users/reactivation/request`): manda email con token (mismo patrón one-shot que reset).
- **Reactivation confirm** (`/users/reactivation/confirm`, Bearer): valida el token y vuelve `is_active=True`.

## Claims

- El tipo de cuenta (`person`/`organization`) determina si el perfil está en `user_profile` o `company_profile` ([account.py:61-98](backend/users-service/src/app/models/account.py#L61-L98)).
- El orquestador de perfil expone `get_profile` (inactivas permitidas) y `get_active_profile` (solo activas), ambos con cache-aside ([get_profile_orchestrator.py:24-77](backend/users-service/src/app/services/user/services/get_profile_orchestrator.py#L24-L77)).
- `GET /v1/users/profiles/{account_id}` no tiene `Depends(get_current_principal)` — es público, y usa `get_active_profile` (no `get_profile`) para que cuentas desactivadas no sean visibles ([user.py](backend/users-service/src/app/api/routes/user.py), [get_profile_by_id.py](backend/users-service/src/app/services/user/use_cases/profile/get_profile_by_id.py)).
- `CurrentUserPerson.created_at`/`CurrentUserOrganization.created_at` se mapean desde `profile_db.created_at` (la fila de `user_profile`/`company_profile`), no desde `Account.created_at` ([mapper.py](backend/users-service/src/app/services/user/helpers/mapper.py)).
- La foto de perfil se sube a través del backend con `storage.upload_file`, no presigned ([upload_profile_photo.py:46-51](backend/users-service/src/app/services/user/use_cases/profile/upload_profile_photo.py#L46-L51)).
- El onboarding tiene 4 pasos + `done` en el enum `OnboardingStep` ([account.py:30-35](backend/users-service/src/app/models/account.py#L30-L35)).
- La deactivación es soft: `is_active=False` + metadata, sin borrar el usuario de Keycloak ([deactivate_current_account.py:27-30](backend/users-service/src/app/services/user/use_cases/account/deactivate_current_account.py#L27-L30)).
- El interés por ciudad es único por `(account_id, city_id)` ([interests.py:30-36](backend/users-service/src/app/models/interests.py#L30-L36)).
- La deactivación dispara un logout best-effort que nunca bloquea la operación ([user.py:177-183](backend/users-service/src/app/api/routes/user.py#L177-L183)).
