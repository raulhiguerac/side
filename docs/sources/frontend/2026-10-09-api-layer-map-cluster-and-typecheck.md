---
title: Capa api por dominio, cluster del feed en mapa, onboarding controlado por el padre y el typecheck que el build no corre
captured-from: conversation
captured-on: 2026-10-09
participants: [author, claude]
---

## Context
Se auditó el front buscando llamadas "plain" al backend y de ahí salió una serie de refactors y bugs. Se mergearon en los PRs #22 (capa `api/`, tipos por dominio, bugs de Ajustes), #23 (cluster en mapas y feed en mapa con scroll infinito) y #24 (onboarding, casts y dos errores de tipos que se colaron en #22/#23).

## Key conclusions
- **Llamadas al backend.** Todo pasa por `api/clients/{users,catalog,properties,avm}.ts` (axios + interceptor de refresh/timeout) y funciones tipadas por dominio en `api/*.ts` y `api/admin/*.ts`, que devuelven `data`. Las rutas salen de `*_ENDPOINTS` (nuevos `usersEndpoints`, `avmEndpoints`). Se importan como namespace (`import * as usersApi from "@/api/users"`) para no chocar con acciones del store y poder mockear el módulo.
- Única llamada axios cruda legítima: el refresh en `api/clients/interceptors.ts`. `ipapi` y los `fetch` a URLs presignadas de storage no son el backend.
- `/auth/logout` está excluido del retry del interceptor: si no, `forceLogout → logout → 401` se encola esperando un refresh que ya terminó y nunca resuelve. `forceLogout` solo actúa con `isAuthenticated`, para que un anónimo en una página pública no termine redirigido a `/`.
- `checkAuth` ahora pasa por el interceptor: recargar con el access token vencido y el refresh vigente ya no desloguea.
- **Tipos.** `types/<dominio>/` (`users`, `feed`, `properties`, `catalog`, `maps`, `pois`, `avm`, `shared`) con `base.ts` cuando son 1-2 tipos y archivos temáticos cuando crecen. Ningún tipo declarado dentro de composables o componentes. `ListingStatus`/`PropertyType`/`ListingType`/`VerificationStatus` viven en `properties/base.ts`.
- **Ajustes.** La foto de perfil se descartaba sin subirse; ahora va a `POST /v1/users/me/profile/photo` (`useProfileSettings`), validada como el backend (jpeg/png/webp, 5 MB; 413/415 con mensaje), con aviso de fallo parcial. `FormMessage` (`variant`, `role="alert"`) es el patrón para errores/éxitos en formularios.
- **Borrado de cuenta.** users-service no implementa borrado (no hay `DELETE /v1/users/me`): el botón, el modal y la lógica quedan comentados en `SettingsAccount.vue`. `GET /v1/users/me/` se corrigió a `/v1/users/me`.
- **Feed en mapa.** El mapa pinta todo el bbox (el backend ya lo devuelve completo) y `useMarkerCluster` agrupa para que los iconos no se superpongan; la lista hace scroll infinito por tandas de 20 sin requests extra (`useInfiniteScroll`, IntersectionObserver + `recheck`). `sortForMap` reemplaza `Math.random()`: promocionadas, luego distancia al centro del bbox, desempate por id.
- **Cluster maker.** `useMarkerCluster` (attach/sync por diferencias/highlight/detach) es genérico: lo usan propiedades y POIs. Los iconos lucide salen de `markerIconMap` vía `renderToElement` y se cachean como HTML por tipo+estado. `@vue-leaflet` no tiene componente de cluster: lo agrupable es imperativo; solo el `subject` del AVM queda como `<l-marker>` con `<l-icon>` (vue-leaflet tipa `icon` como `Icon`, no acepta `DivIcon`).
- **Bug del zoom.** vue-leaflet actualiza el `v-model:zoom` en un `moveend` con debounce: leerlo en nuestro `moveend` da el zoom anterior. Tras un click en una burbuja se pedía H3 r7 sobre un bbox chico y volvía `[]`. Se lee `map.getZoom()` del evento. Además `useFeedMap` descarta respuestas de bbox viejos (`latestRequest`).
- **Onboarding.** El padre controla el modal: `App.vue` solo tiene `isOnboardingOpen`; `OnboardingModal` pinta el paso con `v-if`; los selectores emiten `submit` y reciben `saving`. `useOnboarding` quedó sin estado de módulo ni imports de componentes (se cortó un import circular). `OnboardingStep` es una unión y los stores se mutan con `setOnboardingStep`/`setLocalities`.
- **Casts.** Los params de ruta son props (`props: true`); `useUrlFilters<T>` y `FilterTabs` (`generic="V"`) son genéricos; `ColumnMeta` de TanStack aumentado con `align` en `types/shared/table.ts`. Se aceptan como normales los `$event.target as HTMLInputElement` y las limitaciones conocidas de TS/Vue.
- **El build no typecheckea los `.vue`** (confirmado inyectando un error: pasa con un warning de eslint). `tsc` solo cubre `.ts`. La única verificación real es `npx -p vue-tsc@2 -p typescript@5.6 vue-tsc --noEmit -p tsconfig.json`; sin correrlo, #22 y #23 se mergearon con un error de tipos cada uno.
- `eslint src` sin `--ext .ts,.vue` no revisa los `.vue`.
- PRs en inglés (se tradujeron #4, #9, #10, #12–#24); sin atribución a Claude en commits ni PRs.

## Open questions
- Idioma de los commits de acá en adelante (los recientes están en español, los PRs ahora en inglés).
- Borrado real de cuentas: feature cross-servicio (Keycloak, perfil, publicaciones, fotos, habeas data) que merece ADR.
- Al pasar el mouse por un marcador cuya tarjeta no está pintada todavía, hoy no pasa nada; ¿saltar o cargar hasta ella?

## Next steps
- `ResetPasswordView.vue:51`: el form llama a `loginUser`, que no existe (es `resetPasswordUser`); Enter rompe.
- Script `typecheck` con vue-tsc fijado en `package.json` y en `scripts/audit.sh`; dejar `vue-tsc` en 0 arreglando `AdminModerationForm.vue:52/:81`.
- Errores de onboarding e `IntentSelector` no se muestran al usuario; migrar los ~31 mensajes de error hechos a mano y el último `alert()` (`DeletePropertyModal`) a `FormMessage`.
- Mover `useLocation`/`useCities`/`useNeighborhoodLookup`/`useProfileListings` fuera de `composables/` (no son composables); `utils/storage.ts` tipado para `localStorage`/`sessionStorage`.
- Constante `DEFAULT_MAP_CENTER` (hoy repetida en `MapUser`, `MapView`, `AvmView`).
- Test runner, empezando por `sortForMap`, `cityIdsOf`, `markerIcon` y `api/` con el cliente mockeado.
