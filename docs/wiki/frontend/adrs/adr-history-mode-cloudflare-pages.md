---
title: ADR-0015 — History mode y el front en Cloudflare Pages con dominio propio
status: stable
last-verified: 2026-10-17
owners: [frontend]
related:
  - "[[adr-hash-history-static-hosting]]"
  - "[[adr-stateless-cluster-external-data]]"
  - "[[project-roadmap-2026]]"
  - "[[frontend]]"
  - "[[frontend-architecture]]"
  - "[[frontend-local-dev]]"
  - "[[users-service-auth]]"
sources: []
decision-date: 2026-10-17
decision-status: accepted
---

# ADR-0015 — History mode y el front en Cloudflare Pages con dominio propio

Reemplaza a [[adr-hash-history-static-hosting]].

## Contexto

[[adr-hash-history-static-hosting]] eligió `createWebHashHistory()` porque el destino era "un bucket estático cualquiera": con `#/` el servidor siempre recibe `/` y no hace falta configurar un fallback a `index.html`.

Dos cosas cambiaron:

- **El destino ya no es genérico.** Desde el 2026-10-05 la demo va detrás de Cloudflare (DNS, CDN, WAF y Tunnel hacia GKE) y el front iba "en Pages o R2" ([[project-roadmap-2026]], [[adr-stateless-cluster-external-data]]).
- **Los correos de users-service no llegan a la app.** `build_redirect_url` arma `FRONT_BASE_URL + "/reset-password?token=…"` (y `/reactivate?token=…`). Con hash, vue-router solo lee lo que va después del `#`, así que la SPA carga en `/` y el token se pierde. Meter `#/` en `FRONT_BASE_URL` tampoco sirve: el helper usa `urljoin`, que descarta el fragmento del base.

Además, Tunnel en el plan gratis exige que la zona del dominio esté en Cloudflare, así que el DNS del dominio propio ya iba a vivir ahí.

## Decisión

El router usa `createWebHistory()` (URLs sin `#`), y el front se sirve desde **Cloudflare Pages** con el dominio propio como custom domain (`app.<dominio>`), con la zona DNS en Cloudflare.

- **DNS:** el dominio se agrega como zona en Cloudflare y se cambian los nameservers en el registrador. El registro del dominio no se mueve.
- **Fallback:** Pages sirve `index.html` en cualquier ruta que no sea un archivo siempre que el build no traiga un `404.html` en la raíz. `frontend/public/` no lo tiene.
- **Topología:** `app.<dominio>` → Pages, `api.<dominio>` → Tunnel → GKE, `cdn.<dominio>` → R2 público. El `.pages.dev` queda como URL secundaria.

## Alternativas consideradas

- **Seguir con hash y que el back meta `/#/` en los links** — arregla los correos, pero exige reescribir `build_redirect_url` sin `urljoin` y mantiene las desventajas de [[adr-hash-history-static-hosting]] (SEO, analytics, URLs que se comparten mal) en un host que ya no las necesita.
- **R2 como bucket público** — sirve los archivos, pero no tiene fallback de SPA: hace falta una regla de rewrite o un Worker. Es armar Pages a mano.
- **Contenedor nginx en el cluster** — `try_files` resuelve el fallback y el front viaja con el Helm al VPS, pero gasta crédito de GKE, cada deploy es build de imagen + rollout y el front cae cuando cae el cluster. El front es estático: no gana nada estando dentro.
- **Pages solo con `.pages.dev`** — sin dominio propio, el front y la API quedan en sitios distintos y la cookie de sesión deja de ser same-site.

## Consecuencias

- ✅ Los links de los correos funcionan sin tocar `build_redirect_url`; solo falta corregir `FRONT_BASE_URL`, que no tiene esquema ni TLD ([[open-items]]).
- ✅ URLs limpias: mejor para compartir, SEO y analytics.
- ✅ Front y API en subdominios del mismo dominio: la cookie puede ir con `Domain=.<dominio>` y `SameSite=Lax`, con CORS de origen exacto.
- ✅ Deploy sin operación: Pages publica en cada push y da previews por PR.
- ❌ El front depende de un host con fallback de SPA. Si sale de Pages (VPS, otro CDN), el destino necesita su rewrite (`try_files $uri /index.html` en nginx).
- ❌ Agregar un `404.html` en `public/` apaga el fallback de Pages y rompe toda ruta profunda.
- ❌ Una ruta inexistente responde `200` con la SPA, y el router no tiene catch-all: se ve una página vacía. Era igual con hash.
- ❌ En dev, el fallback de webpack-dev-server solo responde a peticiones con `Accept: text/html`; un `curl` pelado a una ruta profunda da `404`, el navegador no.

## Claims

- `vue-router` se crea con `createWebHistory(process.env.BASE_URL)` ([router/index.ts:13](frontend/src/router/index.ts#L13)).
- `frontend/public/` no contiene `404.html` ([public/](frontend/public)).
- `vue.config.js` no define `publicPath`, así que los assets se sirven con ruta absoluta (`/js/app.js`) y cargan desde rutas anidadas ([vue.config.js](frontend/vue.config.js)).
- El router no declara una ruta catch-all (`/:pathMatch(.*)*`) ([router/routes/](frontend/src/router/routes)).
- `build_redirect_url` arma el link con `urljoin(FRONT_BASE_URL, path)`, sin `#` ([url_builder.py:13](backend/users-service/src/app/services/shared/helpers/url_builder.py#L13)).
