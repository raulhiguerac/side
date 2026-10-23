---
title: Entrega del front (variables de build, CI/CD con wrangler) y alcance del provider de Cloudflare para Terraform
captured-from: conversation
captured-on: 2026-10-17
participants: [author, claude]
---

## Context
Con el front decidido en Cloudflare Pages con dominio propio ([[adr-history-mode-cloudflare-pages]]), se discutió cómo llegan los valores de producción al bundle, cómo sería el CI/CD y cuánto de Cloudflare se puede manejar con Terraform.

## Key conclusions
- **Las `VUE_APP_*` se fijan al compilar, no al servir.** `vue-cli-service build` las mete en el JS (y `VUE_APP_GMAPS_KEY` en `public/index.html`). Pages no inyecta nada en runtime. Solo `.env.development` está versionado. Sin variables en el build, `config/index.ts` cae a `/api/*`, que en Pages respondería el fallback con `index.html`.
- **Los valores de producción no van en el repo** (no hay `.env.production`). Viven en el Environment `production` de GitHub:
  - **Variables:** `VUE_APP_USERS_URL`, `_CATALOG_`, `_PROPERTIES_`, `_AVM_`, `_IPAPI_` y `CLOUDFLARE_ACCOUNT_ID`.
  - **Secrets:** `VUE_APP_GMAPS_KEY` y `CLOUDFLARE_API_TOKEN`.
  - El paso de build las pasa como `env:`; Vue CLI las lee del entorno sin archivo.
- **La key de Maps es pública igual:** queda en el bundle. Lo que la protege es restringirla por HTTP referrer (`app.<dominio>`) en Google Cloud.
- **CD del front desde GitHub Actions, no con la integración Git de Pages,** porque esa publica en cada push sin mirar el CI.
  - El job de deploy (`needs` del CI, solo en `main`) baja el `dist/` que construyó el CI y corre `npx wrangler pages deploy dist --project-name=<proyecto>`.
  - Usa `CLOUDFLARE_API_TOKEN` con permiso mínimo: *Account → Cloudflare Pages → Edit*.
- **CD del back por GitOps:** el CI construye y sube la imagen al registry y cambia el tag en el repo de manifiestos; Argo sincroniza desde el cluster. GitHub no tiene credenciales del cluster.
- **Lo que cubre el provider de Cloudflare para Terraform** (v5):
  - zona y settings;
  - `cloudflare_dns_record`;
  - `cloudflare_pages_project` y `cloudflare_pages_domain` (con variables de entorno por entorno);
  - tunnel y config (`cloudflare_zero_trust_tunnel_cloudflared` y `..._config`, cuyo token se pasa como Secret al `cloudflared`);
  - `cloudflare_r2_bucket` y `cloudflare_r2_custom_domain`, más el CORS del bucket;
  - `cloudflare_ruleset` (rate limit, rewrites);
  - Zero Trust Access.
  - El `tfstate` puede vivir en R2 con el backend `s3`.
- **Lo que no cubre:** el cambio de nameservers en el registrador, subir el contenido de Pages, los objetos de R2 y el Deployment de `cloudflared`, que va con Helm y Argo.
- **Cuidados con el provider v5:** renombró recursos respecto a v4 (por ejemplo `cloudflare_record` pasó a `cloudflare_dns_record`) y saca versión cada 2–3 semanas. Hay que fijar la versión exacta y revisar el esquema en el Registry. Tuvo releases solo para arreglar diffs recurrentes en `cloudflare_ruleset`.

## Open questions
- Forma de la API por fuera:
  - un subdominio por servicio, o
  - un solo `api.<dominio>` enrutado por path, que necesita rewrite en el borde porque los servicios exponen `/v1/...` sin prefijo.

  Esto bloquea los valores de `VUE_APP_*_URL` y las reglas del tunnel.
- Adoptar Terraform para el borde. Se ofreció un ADR, sin confirmar.

## Next steps
- Workflow del front: lint, `vue-tsc` y build, más el deploy con wrangler. Vitest cuando exista. Corresponde a los pasos 4 y 6 de "Camino del front a production grade" en [[open-items]].
- Crear el Environment `production` en GitHub con las variables y secrets de arriba.
- Restringir la key de Maps por referrer.
