---
title: Foundational Q&A — frontend
captured-from: conversation
captured-on: 2026-05-21
participants: [author, claude]
---

## Context

Primera sesión de captura del frontend (Vue 3 SPA). El más "verde" de los servicios documentados: stack con varias decisiones puestas como deuda técnica + features completas en código pero pausadas en backend + algunas libs zombies para limpiar. Foco del wiki: capturar lo que sí funciona end-to-end y marcar el resto como open items.

## Key conclusions

### Funcional end-to-end al 2026-05-21
- **Login + Register**: pegan al backend real (users-service vía cookie JWT). Error handling pobre, mejorable.
- **Settings (profile/security/account)**: respaldados por UCs en `users-service` (wiki de ese servicio pendiente).
- **Auth pattern**: cookie-based, `withCredentials: true` en todas las calls. Sin interceptor central — cada store maneja 401 a mano.

### Scaffolding visual (sin backend correspondiente)
- `/properties/mine` — ruta existe pero **no hay endpoint** en properties-service; sería un UC nuevo a implementar.
- `/dev` DevPlayground — sandbox del autor para probar componentes; no es producto.

### Onboarding
- **Frontend completo**: modal de 4 pasos (`intent → city → neighborhood → property_type`), dispara con cambio de `isAuthenticated` en `App.vue`, dismiss persistible vía `sessionStorage`.
- **Backend pausado** ([[project_current_priorities]]) pero parte del UC existe. Necesita un **refactor pequeño en users-service** para que el source-of-truth de localities/neighborhoods sea `catalog-service` (hoy se duplica o no se valida contra catalog).

### Stack decisions
- **Vue CLI 5 (webpack)**: deuda técnica reconocida, Vue CLI en maintenance. **Plan: migrar a Vite cuando todos los microservicios backend estén cerrados.**
- **Hash history (`/#/`)**: deliberado. Deployment planificado en **bucket estático público con build compilado** — sin rewrite rules. SEO no es prioridad MVP.
- **Firebase 10**: era un spike-out que no funcionó. **Eliminar todo lo relacionado** (imports en `LoginView.vue`, dep del `package.json`, endpoint `/v1/auth/login/google` del backend si solo lo usaba esta integración).
- **Mapa**: Leaflet (`@vue-leaflet/vue-leaflet`) + **D3.js** para render y overlays. **No Mapbox para mapas.**
- **Mapbox**: solo para forward geocoding (autocomplete address → lat/lon). Alinea con [[adr-mapbox-frontend-only]] de catalog.

### API consumption
- **Axios sin instance centralizada**: algunas calls hardcodean URLs (`auth.ts` → `http://localhost:8000/...`), otras usan `API.USERS_BASE_URL` / `CATALOG_BASE_URL` de `config/index.ts`.
- **Plan**: una axios instance única con interceptor (401 → logout, env vars siempre, baseURL configurada).
- Pinia stores y composables hacen HTTP directo — no hay capa de "service layer" explícita.
- **Caching local agresivo**: `localStorage` para countries (semi-permanente), `sessionStorage` para cities/neighborhoods por id.

### Local dev
- `npm run serve` (vue-cli-service, port **8080** default).
- CORS del backend abierto (`allow_origins=["*"]`) — temporal mientras se prueba todo, se cierra antes de producción.

## Open questions

- Cuándo cerrar CORS (timing del backend) y cómo coordinarlo con frontend (probablemente requiere CORS configurable por env, no global).
- Lista exacta de endpoints que el wizard de onboarding del backend necesita implementar.

## Next steps

- Wiki frontend (~7 páginas):
  - Batch 2: `frontend.md` overview + `frontend-architecture.md`
  - Batch 3: `frontend-onboarding-flow.md` + 4 ADRs (Vue CLI deferred, hash history, Leaflet+Mapbox split, Firebase removal) + `runbook/frontend-local-dev.md`
- Open items operativos a trackear:
  - Refactor de onboarding en users-service: acoplar a catalog como source-of-truth.
  - Remover Firebase completo del frontend (deps + código + endpoint backend si aplica).
  - Centralizar axios con instance + interceptor; eliminar URLs hardcoded en `auth.ts`.
  - Migrar Vue CLI → Vite post-backend completion.
  - Cerrar CORS pre-producción.
