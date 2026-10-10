---
title: "ADR-0013 — Todo el HTTP del front pasa por funciones tipadas de api/, por dominio"
status: stable
last-verified: 2026-10-09
owners: [frontend]
related:
  - "[[frontend-architecture]]"
  - "[[frontend-admin-panel]]"
  - "[[frontend-onboarding-flow]]"
  - "[[open-items]]"
sources: [../../../sources/frontend/2026-10-09-api-layer-map-cluster-and-typecheck.md]
decision-date: 2026-10-09
decision-status: accepted
---

# ADR-0013 — Todo el HTTP del front pasa por funciones tipadas de api/, por dominio

## Contexto

La auditoría de llamadas al backend del 2026-10-09 encontró tres problemas:

- **Llamadas "plain".** `checkAuth`, `logout` y el intent del onboarding usaban `axios` crudo, sin el interceptor de refresh ni el timeout de los clientes. Con el access token vencido, el intent fallaba en silencio y una recarga desloguea aunque el refresh siguiera vigente.
- **Rutas a mano.** Unas 25 rutas `/v1/...` estaban escritas en composables, stores, componentes y vistas. users y avm no tenían constantes de endpoints.
- **HTTP en 14 vistas y componentes**, con `usersApi.post("/v1/...")` directo. No había un lugar único donde mockear el backend para testear.

Los clientes por servicio (`usersApi`, `propertiesApi`, …) ya existían; lo que faltaba era la capa encima.

## Decisión

**Todo el HTTP vive en `src/api/`, en dos niveles.**

- **Clientes** en `api/clients/{users,catalog,properties,avm}.ts`: una instancia de axios por servicio con su interceptor. Nadie fuera de `api/` los importa.
- **Funciones por dominio** en `api/{users,catalog,properties,avm}.ts` y `api/admin/{properties,catalog}.ts`: una función por endpoint. Cada una toma la ruta de `*_ENDPOINTS`, recibe y devuelve tipos de `types/` y retorna `data`, no la respuesta de axios. Las conversiones de payload (camelCase → snake_case, campos opcionales omitidos) viven acá.

Se importan como namespace (`import * as usersApi from "@/api/users"`). Así no chocan con acciones del store que se llaman igual (`login`, `logout`) y un test puede mockear el módulo entero.

**Componentes y vistas pueden llamar a una función de `api/` para acciones puntuales sin estado**, como borrar una propiedad o cargar un detalle. Lo que tiene estado (loading, error, paginación, varios pasos) va a un composable.

Las únicas llamadas HTTP fuera de los clientes son el refresh del interceptor (no puede pasar por sí mismo), `ipapi.co` (servicio externo) y los `fetch` a URLs presignadas de storage (la firma va en la URL y no deben llevar cookies).

## Alternativas consideradas

- **Que los composables llamen directo al cliente** (lo que había en el admin). Es menos código, pero la ruta y el shape del payload quedan repartidos y no hay un único punto que mockear.
- **Todo por composables, nunca `api/` desde un componente.** Es más uniforme, pero obliga a crear 8–10 composables triviales que solo envuelven una llamada.
- **Un cliente `adminApi` propio.** Ya se había descartado ([[frontend-admin-panel]]): "admin" no es un servicio. `api/admin/` son funciones sobre los clientes de properties y catalog.

## Consecuencias

- Una ruta del backend cambia en un solo lugar (`*_ENDPOINTS`), y su shape en una sola función.
- Las funciones de `api/` se pueden testear con el cliente mockeado. Composables y componentes se testean mockeando `api/<dominio>`.
- `checkAuth` pasa por el interceptor. Para que un anónimo no termine redirigido a `/`, `forceLogout` solo actúa con sesión, y `/auth/logout` se excluyó del retry (si no, el logout tras un refresh fallido se colgaba en la cola).
- Es una capa más entre el componente y axios. Para una sola llamada sin estado se acepta llamarla desde el componente en vez de sumar un composable.

## Claims

- Ningún archivo fuera de `src/api/` importa un cliente de `src/api/clients/` ([api/](frontend/src/api)).
- `api/users.ts`, `api/catalog.ts`, `api/properties.ts`, `api/avm.ts` y `api/admin/*.ts` toman sus rutas de `constants/*Endpoints.ts` ([api/](frontend/src/api), [constants/](frontend/src/constants)).
- Ninguna ruta `/v1/...` aparece fuera de `constants/*Endpoints.ts` en `src/` ([constants/](frontend/src/constants)).
- `AUTH_ENTRYPOINTS` del interceptor incluye login, register y logout ([api/clients/interceptors.ts:29-33](frontend/src/api/clients/interceptors.ts#L29-L33)).
- `forceLogout` solo llama a `authStore.logout()` si `authStore.isAuthenticated` ([api/clients/interceptors.ts:35-39](frontend/src/api/clients/interceptors.ts#L35-L39)).
