---
title: Runbook — frontend local dev
status: draft
last-verified: 2026-10-04
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
  - ../../../sources/_shared/2026-09-07-entorno-dev-migrable.md
  - ../../../sources/frontend/2026-09-28-catalog-tabs-and-production-readiness.md
  - ../../../sources/frontend/2026-10-04-admin-neighborhoods-tab.md
---

## TL;DR

> **Actualizado 2026-09-27 — las apps vuelven a correrse a mano.** `make bootstrap && make up`
> levanta solo la infra: los servicios de aplicacion y los seeds estan comentados en
> `docker-compose.yml`, y cada server se arranca dentro del devcontainer. Este runbook
> sirve de referencia para eso; ante diferencias, manda el [`README.md`](README.md).

Mismo patrón devcontainer-first que los backends. Dentro del devcontainer: `cd frontend && npm install && npm run serve` → SPA en **`http://localhost:8080/#/`**. Backend en `:8000` (users), `:8001` (catalog) — corren a mano desde el devcontainer en terminales separadas. CORS abierto temporalmente. Ningún tooling de tests/e2e configurado todavía.

## Prerequisites

- Docker Desktop corriendo.
- VS Code con extensión **Dev Containers**.
- Repo clonado, `.env.local` completado y `make bootstrap` corrido.
- `frontend/.env.development` versionado con las URLs de los servicios; la key de Google Maps va en `.env.local`.
- **Node 24 y pnpm/npm** ya vienen en la imagen del devcontainer ([.devcontainer/Dockerfile](.devcontainer/Dockerfile)). No instalar Node en el host.

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
VUE_APP_AVM_URL=http://localhost:8003
VUE_APP_PROPERTIES_URL=http://localhost:8002
VUE_APP_IPAPI_URL=https://ipapi.co/json/
```

Notas:
- **Gap 2026-10-04:** `frontend/.env.development` sí define las cuatro `VUE_APP_*_URL` apuntando a `localhost:800x`, así que en dev hoy el front llama directo y el proxy no se usa. La intención es el proxy; ver known gap 11.
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

## CORS

Con `withCredentials: true` el navegador no acepta `Access-Control-Allow-Origin: *`: exige el origen exacto y `Access-Control-Allow-Credentials: true`. Por eso catalog (desde 2026-10-04) y properties declaran `allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"]` con `allow_credentials=True` ([catalog main.py:18-24](backend/catalog-service/src/app/main.py#L18-L24)). Los orígenes están fijos en código; para staging/prod tienen que venir de configuración.

Si CORS bloquea (`The value of the 'Access-Control-Allow-Credentials' header … must be 'true'`):
- El front está llamando directo al backend en vez de pasar por el proxy (ver known gap 11).
- El backend no tiene `allow_credentials=True` o no lista el origen del front.
- Si el front cambia de puerto/host, hay que sumarlo a la lista de orígenes.

## Build para producción

```bash
cd /workspace/frontend
npm run build
```

Salida: `dist/` con assets estáticos. Deploy planeado en bucket público (ver [[adr-hash-history-static-hosting]]). **Update 2026-09-28:** el destino no está definido. La alternativa en exploración es servir `dist/` desde el clúster de `infra/k8s`, con `/api/*` en el Gateway; si se elige, ese ADR queda superseded.

⚠️ **Hoy `npm run build` falla**: `vue-cli-service build` corre ESLint y aborta ([[open-items]]).

**Sin pipeline de CI/CD al 2026-09-28**: no existe `.github/workflows`, así que ni lint, ni typecheck, ni build corren solos.

## Linting

```bash
npm run lint
```

Configurado con ESLint + `@vue/eslint-config-typescript` + Prettier. Hay un `.eslintrc.js` en el root del frontend.

## Tests

**Sin tooling de tests ni de typecheck al 2026-09-28**:
- No `vitest` ni `@vue/test-utils` en `devDependencies`.
- No `vue-tsc`: nada chequea tipos fuera del editor.
- No directorio `tests/` ni `__tests__/`.
- No script `test` en `package.json`.

El camino propuesto (Vite antes que Vitest, tests en composables y utils, CI por PR) está en [[open-items]], en "Camino del front a production grade".

## Known gaps (actualizado 2026-10-04)

1. **`auth.ts` (store Pinia) hardcodea URLs** — usa `usersApi` pero el store de Keycloak puede quedar desincronizado si cambia el host. Menor riesgo ahora que las instancias están centralizadas.
2. ~~**Sin axios instance central**~~ — **resuelto** (2026-06-28): instancias dedicadas por servicio + interceptor de silent refresh. Ver [[frontend-architecture]] sección "API consumption pattern".
3. **Sin tests** — ningún framework configurado.
4. ~~**CORS abierto**~~ — **resuelto** parcialmente: catalog y properties declaran orígenes explícitos con credenciales (fijos en código). En prod tienen que venir de configuración. El proxy webpack haría las requests same-origin en dev, pero hoy no se usa (gap 11).
5. **Backends a mano** — no hay docker-compose service que arranque users/catalog/analytics automáticamente (se corren manualmente desde el devcontainer).
6. **Firebase residual** — `firebase` aún en deps y usado en `LoginView.loginWithGoogle`. Ver [[adr-firebase-removal]].
7. **`leaflet` y `@vue-leaflet/vue-leaflet` en devDependencies** — debería ser `dependencies` si se usa en runtime.
8. **Onboarding completo en frontend, pausado en backend** — ver [[frontend-onboarding-flow]] "El refactor pendiente".
9. **Cursor de paginación del feed no vive en `route.query`** — paginación in-memory, no compartible por URL.
10. **VS Code port-forwarding puede hijackear un puerto de backend individual** (distinto del gotcha de Chrome+proxy de arriba, que ya está resuelto). Síntoma: un endpoint devuelve 400 con body vacío y el log de ese microservicio muestra `WARNING uvicorn.error: Invalid HTTP request received.` sin ninguna línea de acceso normal para esa request — la request nunca llega a FastAPI, se corta a nivel de transporte. Diagnóstico: `lsof -iTCP:<puerto>` — si el proceso que escucha es `code` (VS Code) y no el `fastapi dev`/`uvicorn` esperado, el auto-port-forwarding del devcontainer tomó el puerto y actúa de proxy intermedio que no maneja bien todas las requests (particularmente con cookies/credentials). Fix: panel "Ports" de VS Code → quitar el forward de ese puerto → reiniciar el proceso backend si hace falta para que lo recupere.
11. **`.env.development` saltea el proxy** (2026-10-04) — define `VUE_APP_*_URL=http://localhost:800x` y `config/index.ts` las prefiere sobre `/api/*`. El front llama directo a cada backend y CORS aplica. La intención es el proxy: quitar esas variables del `.env.development`. Ver [[open-items]].
12. **La VM de Docker se queda sin memoria** (2026-10-04) — en macOS Docker Desktop corre en una VM con tope fijo (aquí ~7,7 GB de 16 GB). Con ORS (`-Xmx6g`), MLflow, Keycloak, Kafka y un build de webpack, el kernel de la VM mata procesos (ORS, Kafka, Keycloak, el propio build; `docker inspect` muestra `OOMKilled=true`). Mitigación: build del front en el host o con `NODE_OPTIONS=--max-old-space-size=1536`; subir la memoria de Docker Desktop (Settings → Resources); no levantar ORS/MLflow/Kafka si no se usan.

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
- El devcontainer ([.devcontainer/Dockerfile](.devcontainer/Dockerfile)) incluye Node 24 + uv + pnpm preinstalados.
- `forwardPorts` del devcontainer reenvía 8000-8003, 8080, 8180, 8888, 5050 y 5540 — el 8080 es justo el que usa Vue CLI por default ([devcontainer.json](.devcontainer/devcontainer.json)).
- Backends NO están como service en el compose — se corren manualmente desde dentro del devcontainer (mismo patrón que [[analytics-service-local-dev]] y [[catalog-service-local-dev]]).
- No hay tests configurados (ningún framework de test en `devDependencies`).
- Un `WARNING uvicorn.error: Invalid HTTP request received.` en el log de un backend, junto con un 400 de body vacío en el frontend, indica un problema de transporte (proxy/port-forwarding) antes de descartar el código de la app — verificar con `lsof -iTCP:<puerto>` quién escucha realmente ese puerto.
