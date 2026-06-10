---
title: Runbook — frontend local dev
status: draft
last-verified: 2026-05-21
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[analytics-service-local-dev]]"
  - "[[catalog-service-local-dev]]"
sources: [../../../sources/frontend/2026-05-21-foundational-qa.md]
---

## TL;DR

Mismo patrón devcontainer-first que los backends. Dentro del devcontainer: `cd frontend && npm install && npm run serve` → SPA en **`http://localhost:8080/#/`**. Backend en `:8000` (users), `:8001` (catalog) — corren a mano desde el devcontainer en terminales separadas. CORS abierto temporalmente. Ningún tooling de tests/e2e configurado todavía.

## Prerequisites

- Docker Desktop corriendo.
- VS Code con extensión **Dev Containers**.
- Repo clonado.
- `.env` del root presente (compartido para todos los services).
- **Node 20 y pnpm/npm** ya vienen en la imagen del devcontainer ([.devcontainer/Dockerfile](.devcontainer/Dockerfile)). No instalar Node en el host.

## Levantar el entorno

1. Abrir el repo en VS Code.
2. **Dev Containers: Reopen in Container**.
3. Esperar a que docker-compose levante toda la infra de backends.

El frontend **no se levanta automáticamente** — el `develop` service del compose es el devcontainer, no incluye un proceso de build/serve. Lo arrancás vos.

## Correr el frontend

Dentro del devcontainer:

```bash
cd /workspace/frontend
npm install      # primera vez (o tras cambios en package.json)
npm run serve    # dispara vue-cli-service serve
```

Output esperado:
```
DONE  Compiled successfully in Xms

App running at:
- Local:   http://localhost:8080/
- Network: http://172.17.0.2:8080/
```

Abrir **`http://localhost:8080/#/`** en el browser del host. El `#/` es necesario por el hash history (ver [[adr-hash-history-static-hosting]]).

## Env vars del frontend

`frontend/.env.example` actual:

```bash
VUE_APP_USERS_URL=http://localhost:8000
VUE_APP_CATALOG_URL=http://localhost:8001
VUE_APP_IPAPI_URL=https://ipapi.co/json/
```

Notas:
- Prefijo `VUE_APP_*` lo requiere Vue CLI (Vite usaría `VITE_*`).
- `VUE_APP_USERS_URL` apunta al puerto del **users-service** (no del devcontainer host).
- `VUE_APP_CATALOG_URL` apunta al puerto del **catalog-service**.
- `VUE_APP_IPAPI_URL` es la URL de **ipapi.co** (third-party) usado para detectar el país por IP en `userStore.detectLocation`.

## Levantar los backends necesarios

El frontend hoy necesita **users-service** y **catalog-service** corriendo. En terminales separadas del devcontainer:

**Terminal 1 — users-service** (port 8000):
```bash
cd /workspace/backend/users-service
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — catalog-service** (port 8001):
```bash
cd /workspace/backend/catalog-service
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Ver [[catalog-service-local-dev]] para el detalle de catalog (env vars, seed, cookie JWT testing).

## Probar end-to-end

### Login
1. Abrir `http://localhost:8080/#/login`.
2. Email + password del user creado en Keycloak.
3. Si funciona, redirige a `/#/`.

Detalle del flujo cookie en [[catalog-service-architecture]] sección "Auth en el servicio".

### Catálogo en autocomplete
1. Login.
2. Onboarding modal aparece automáticamente (si no completaste).
3. En el paso `city` (LocalitySelector), tipear texto — debería autocompletar desde el catálogo.
4. Si no autocompleta, verificar:
   - catalog-service corriendo en `:8001`.
   - Catálogo seedeado (ver [[catalog-service-local-dev]] sección Seed).
   - CORS del backend permite `http://localhost:8080`.

### Mapa (cuando se implemente)
Hoy `MapUser.vue` existe pero su integración es limitada — no hay endpoints backend de listings con coordenadas todavía.

## CORS — abierto temporal

Backends hoy tienen `allow_origins=["*"]` (ver, ej., [main.py:18-23](backend/catalog-service/src/app/main.py#L18-L23) de catalog). Eso es **temporal mientras se prueba todo**. Pre-producción se cerrará a la lista de orígenes reales.

Si CORS empieza a bloquear:
- Verificar que el backend tiene `allow_origins=["*"]` (puede haberse cambiado).
- Verificar que axios envía `withCredentials: true` (todas las calls del front lo hacen).
- Si el frontend cambia de puerto/host, el CORS no es relevante hoy (wildcard) pero lo será cuando se cierre.

## Build para producción

```bash
cd /workspace/frontend
npm run build
```

Salida: `dist/` con assets estáticos. Deploy planeado en bucket público (ver [[adr-hash-history-static-hosting]]).

**Sin pipeline de CI/CD configurado al 2026-05-21** — el build se hace a mano cuando toque deployar.

## Linting

```bash
npm run lint
```

Configurado con ESLint + `@vue/eslint-config-typescript` + Prettier. Hay un `.eslintrc.js` en el root del frontend.

## Tests

**Sin tooling de tests configurado al 2026-05-21**:
- No `vitest` ni `@vue/test-utils` en `devDependencies`.
- No directorio `tests/` ni `__tests__/`.
- No script `test` en `package.json`.

Worth flag para cuando se priorice testing — gap conocido.

## Known gaps (2026-05-21)

1. **`auth.ts` hardcodea `http://localhost:8000`** — bug en cuanto `VUE_APP_USERS_URL` cambie (staging/prod). Ver [[frontend-architecture]] sección "API consumption pattern".
2. **Sin axios instance central** — interceptor 401 manual en cada store.
3. **Sin tests** — ningún framework configurado.
4. **CORS abierto** — pre-producción debe cerrarse.
5. **Backends a mano** — no hay docker-compose service que arranque users/catalog/analytics automáticamente (se corren manualmente desde el devcontainer).
6. **Firebase residual** — `firebase` aún en deps y usado en `LoginView.loginWithGoogle`. Ver [[adr-firebase-removal]].
7. **`leaflet` y `@vue-leaflet/vue-leaflet` en devDependencies** — debería ser `dependencies` si se usa en runtime.
8. **Onboarding completo en frontend, pausado en backend** — ver [[frontend-onboarding-flow]] "El refactor pendiente".

## Comandos útiles

```bash
# Re-instalar deps después de cambios al package.json
npm install

# Ver el bundle size resultante
npm run build -- --report   # genera dist/report.html (webpack-bundle-analyzer)

# Limpiar caché del browser para testing flow auth
# (en DevTools → Application → Storage → Clear site data)

# Forzar refresh de los stores Pinia en runtime
# (en DevTools console)
> window.location.reload()
```

## Claims

- Script `npm run serve` invoca `vue-cli-service serve`, port default 8080 ([package.json:6](frontend/package.json#L6)).
- Script `npm run build` invoca `vue-cli-service build` y produce `dist/` ([package.json:7](frontend/package.json#L7)).
- Env vars del frontend usan prefijo `VUE_APP_*` (requerido por Vue CLI 5) ([.env.example](frontend/.env.example)).
- `.env.example` declara `VUE_APP_USERS_URL`, `VUE_APP_CATALOG_URL`, `VUE_APP_IPAPI_URL` — sin Firebase, sin MAPBOX, sin Sentry/analytics.
- El devcontainer ([.devcontainer/Dockerfile](.devcontainer/Dockerfile)) incluye Node 20 + uv + pnpm preinstalados.
- El `develop` service del compose forwarda los ports 8000, 5173, 8080 — el 8080 es justo el que usa Vue CLI por default ([docker-compose.yml:10-12](docker-compose.yml#L10-L12)).
- Backends NO están como service en el compose — se corren manualmente desde dentro del devcontainer (mismo patrón que [[analytics-service-local-dev]] y [[catalog-service-local-dev]]).
- No hay tests configurados al 2026-05-21 (ningún framework de test en `devDependencies`).
