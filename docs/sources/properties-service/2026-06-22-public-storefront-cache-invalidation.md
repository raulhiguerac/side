---
title: Cache-aside + invalidación por prefijo para la vitrina pública de propiedades
captured-from: conversation
captured-on: 2026-06-22
participants: [raul, claude]
---

## Context

Se implementó el cache de la **vitrina pública de un publicante** (`GET /v1/properties/users/{user_id}`, UC `GetPublicUserPropertiesUseCase`) con paginación por offset, y se resolvió cómo invalidarla cuando cambian las propiedades del dueño. Distinta de `GetMyPropertiesUseCase` (`/me`): la pública filtra `status == active` y toma el `user_id` del path sin auth; la de "mis propiedades" usa `principal.sub` del JWT y devuelve todos los estados.

## Key conclusions

- **Cache-aside con offset en la key**: `properties:user:{id}:public:{offset}` (helper `public_user_properties(user_id, offset)`). El offset entra a la key porque cada página es una entrada distinta; sin él, la página 2 devolvería la data cacheada de la página 1.
- **Diseño elegido: offset a nivel query** (repo `LIMIT/OFFSET`) en vez de cachear la lista completa y cortar en memoria. Justificado por set acotado (un publicante rara vez supera ~20 activas). Costo asumido: la invalidación pasa a ser un wipe por prefijo, no una key exacta.
- **Page size en settings**: `PUBLIC_PROPERTIES_PAGE_SIZE = 20` (antes hardcodeado como `.limit(20)` en el adapter).
- **Se cachea también el resultado vacío** (`if cached is not None`, no `if cached`) para evitar cache penetration de usuarios sin listings — `[]` es un hit válido; con el chequeo truthy nunca se leía.
- **`delete_pattern(pattern)` nuevo en el stack de cache**: SCAN iterativo (no `KEYS`, que bloquea Redis) + `DEL`, con guard `if keys`. Agregado en `CacheClient` (integración), `CachePort` (port) y `RedisCacheAdapter` (adapter). Degrada silencioso (return `None`), igual que el resto de operaciones de cache.
- **Helper de patrón**: `public_user_properties_pattern(user_id)` → `properties:user:{id}:public:*`.
- **Por qué prefijo y no key exacta**: con paginación por offset, un cambio de membresía corre la posición de **todas** las propiedades siguientes → desalinea todas las páginas, no solo la que contiene la propiedad afectada. Además no se trackea en qué offset cayó cada una. Por eso se borra todo el prefijo del dueño y se re-cachea on-demand.
- **Invalidación proactiva en 8 UCs de escritura**, junto a las keys exactas que ya borraban `client_properties`: `delete_property`, `set_property_visibility`, `update_property`, `confirm_image_uploads`, `delete_property_images`, `moderation/set_status`, `promotions/create`, `promotions/delete`. Cada uno hace dos operaciones: `delete([keys exactas])` + `delete_pattern(prefijo público)`.
- **Excluidos a propósito**: `verify` (la card no expone `verification_status`) y `create_property` (nace `draft`, no entra al set público hasta publicarse, donde `set_visibility`/`set_status` ya invalidan).
- **Criterio de inclusión**: un UC invalida la vitrina si cambia la **membresía** del set activo (`status==active`) o un **campo que `PropertyCardSchema` renderiza** (precio/datos, fotos con `is_cover`, `is_promoted`).
- **Bug de DI corregido**: el provider `get_public_user_properties_uc` no inyectaba `cache` tras agregarlo al `__init__` → la request quedaba stalled (mismo patrón que el bug de la isócrona en catalog-service).

## Open questions

- **Invalidación sobre draft**: en `update_property`/imágenes sobre un draft, el `delete_pattern` corre igual (wipe de más, inofensivo — re-cachea lo mismo). Se aceptó no ramificar por status.
- **Polución de cache**: cacheando vacíos + offset en la key, offsets arbitrarios (`?offset=99999`) pueblan entradas vacías en Redis. Acotado por el TTL de 30 min (`CACHE_TTL_USER_PROPERTIES_SECONDS`); aceptable a la escala actual.

## Next steps

- Documentar la estrategia en la wiki (este capture la ingesta).
- (Pendiente aparte, no relacionado) Composable del detail view del frontend.
