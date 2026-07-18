---
title: Runbook — frontend local dev
status: draft
last-verified: 2026-07-13
owners: [frontend]
related:
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[analytics-service-local-dev]]"
  - "[[catalog-service-local-dev]]"
sources:
  - ../../../sources/frontend/2026-05-21-foundational-qa.md
  - ../../../sources/frontend/2026-06-28-devcontainer-proxy-chrome-fix.md
  - ../../../sources/frontend/2026-07-13-vscode-port-forwarding-breaks-requests.md
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

Las vars `VUE_APP_*_URL` son **opcionales en dev** — si no están seteadas, `config/index.ts` usa los paths del proxy (`/api/users`, `/api/catalog`, etc.) que webpack redirige automáticamente.

```bash
# Solo necesarias para staging/prod o para apuntar a un backend remoto:
VUE_APP_USERS_URL=http://localhost:8000
VUE_APP_CATALOG_URL=http://localhost:8001
VUE_APP_AVM_URL=http://localhost:8002
VUE_APP_PROPERTIES_URL=http://localhost:8003
VUE_APP_IPAPI_URL=https://ipapi.co/json/
```

Notas:
- Prefijo `VUE_APP_*` lo requiere Vue CLI (Vite usaría `VITE_*`).
- `VUE_APP_IPAPI_URL` es la URL de **ipapi.co** (third-party) para detectar país por IP.

## Webpack devServer proxy

`vue.config.js` configura un proxy que reenvía `/api/<servicio>/*` → `http://localhost:<puerto>/*` dentro del container. Esto es **necesario para Chrome**: las subresource requests cross-port a `localhost` quedan stalled indefinidamente en Chrome con VS Code devcontainer port forwarding (Firefox no tiene este problema). El proxy hace todo same-origin desde el browser.

**No hay que tocar nada** — funciona solo al arrancar `npm run serve`. Si se agregan nuevos servicios, añadir su entrada en `devServer.proxy`.

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

## Known gaps (actualizado 2026-06-28)

1. **`auth.ts` (store Pinia) hardcodea URLs** — usa `usersApi` pero el store de Keycloak puede quedar desincronizado si cambia el host. Menor riesgo ahora que las instancias están centralizadas.
2. ~~**Sin axios instance central**~~ — **resuelto** (2026-06-28): instancias dedicadas por servicio + interceptor de silent refresh. Ver [[frontend-architecture]] sección "API consumption pattern".
3. **Sin tests** — ningún framework configurado.
4. ~~**CORS abierto**~~ — **resuelto** parcialmente: el proxy webpack hace las requests same-origin en dev. En prod los backends deben tener `allow_origins` cerrado a los dominios reales.
5. **Backends a mano** — no hay docker-compose service que arranque users/catalog/analytics automáticamente (se corren manualmente desde el devcontainer).
6. **Firebase residual** — `firebase` aún en deps y usado en `LoginView.loginWithGoogle`. Ver [[adr-firebase-removal]].
7. **`leaflet` y `@vue-leaflet/vue-leaflet` en devDependencies** — debería ser `dependencies` si se usa en runtime.
8. **Onboarding completo en frontend, pausado en backend** — ver [[frontend-onboarding-flow]] "El refactor pendiente".
9. **Cursor de paginación del feed no vive en `route.query`** — paginación in-memory, no compartible por URL.
10. **VS Code port-forwarding puede hijackear un puerto de backend individual** (distinto del gotcha de Chrome+proxy de arriba, que ya está resuelto). Síntoma: un endpoint devuelve 400 con body vacío y el log de ese microservicio muestra `WARNING uvicorn.error: Invalid HTTP request received.` sin ninguna línea de acceso normal para esa request — la request nunca llega a FastAPI, se corta a nivel de transporte. Diagnóstico: `lsof -iTCP:<puerto>` — si el proceso que escucha es `code` (VS Code) y no el `fastapi dev`/`uvicorn` esperado, el auto-port-forwarding del devcontainer tomó el puerto y actúa de proxy intermedio que no maneja bien todas las requests (particularmente con cookies/credentials). Fix: panel "Ports" de VS Code → quitar el forward de ese puerto → reiniciar el proceso backend si hace falta para que lo recupere.

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
- En dev, si no se setean `VUE_APP_*_URL`, `config/index.ts` usa paths de proxy (`/api/users`, etc.) — el proxy de `vue.config.js` los reenvía al backend correspondiente ([config/index.ts](frontend/src/config/index.ts), [vue.config.js](frontend/vue.config.js)).
- El proxy webpack es obligatorio en Chrome con devcontainer: subresource requests cross-port a localhost quedan stalled indefinidamente por la interacción de VS Code port forwarding con el keep-alive de Chrome ([vue.config.js](frontend/vue.config.js)).
- El devcontainer ([.devcontainer/Dockerfile](.devcontainer/Dockerfile)) incluye Node 20 + uv + pnpm preinstalados.
- El `develop` service del compose forwarda los ports 8000, 5173, 8080 — el 8080 es justo el que usa Vue CLI por default ([docker-compose.yml:10-12](docker-compose.yml#L10-L12)).
- Backends NO están como service en el compose — se corren manualmente desde dentro del devcontainer (mismo patrón que [[analytics-service-local-dev]] y [[catalog-service-local-dev]]).
- No hay tests configurados (ningún framework de test en `devDependencies`).
- Un `WARNING uvicorn.error: Invalid HTTP request received.` en el log de un backend, junto con un 400 de body vacío en el frontend, indica un problema de transporte (proxy/port-forwarding) antes de descartar el código de la app — verificar con `lsof -iTCP:<puerto>` quién escucha realmente ese puerto.
