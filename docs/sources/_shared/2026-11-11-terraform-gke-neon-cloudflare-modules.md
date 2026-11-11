---
title: Terraform de la demo — raíz única con módulos gke, neon, cloudflare y maps
captured-from: conversation
captured-on: 2026-11-11
participants: [author, claude]
---

## Context
Se armó el Terraform de la demo en `sidehq/infra/terraform/`, partiendo del módulo de GKE del proyecto `pde`, y se diseñaron Neon y Cloudflare. Nada se aplicó todavía. Se validó con `terraform validate`, corrido en el contenedor `hashicorp/terraform:1.17.2` porque el devcontainer no tiene `terraform` ni `gcloud`.

## Key conclusions
- **Una sola raíz en `terraform/`**, con `gke`, `neon`, `cloudflare` y `maps` como módulos y un único `init`. Los providers solo se configuran en la raíz (`google` por ADC, `neon` por `NEON_API_KEY`, `cloudflare` por `CLOUDFLARE_API_TOKEN`); los módulos declaran solo `required_providers`. El costo es un solo state; si hace falta separar, se usa `terraform state mv`.
- **El bucket del state se crea a mano** (R2, fuera de Terraform) y es el recurso más protegido, con un token aparte limitado a ese bucket. Por ahora el state es local.
- **Módulo `gke`** (desde `pde`):
  - submódulos `services`, `network`, `cluster` e `identity`, en snake_case;
  - sale Cloud SQL, `buckets`, `repository` (el `docker build` con `local-exec`), los secrets y locals de Airflow, el Helm de Argo y ESO, y los providers `kubernetes`, `helm` y `kubectl`.
- **Red:**
  - CIDR RFC1918: nodos `10.10.0.0/24`, pods `10.20.0.0/20` y services `10.30.0.0/22`;
  - 64 pods por nodo, que en GKE es un /25 por nodo y da 32 nodos.
- **Nodos:**
  - `spot = true` (verificado en el provider `google` 8.11), 1 `e2-standard-2` por defecto;
  - cuenta propia con `roles/container.defaultNodeServiceAccount`.
- **Workload Identity:**
  - activo en el cluster, con `GKE_METADATA` en el pool;
  - solo la KSA `external-secrets/external-secrets` tiene binding a una GSA, con `secretAccessor` y vía `iam_member`; los demás pods no reciben credenciales de GCP;
  - se suma la API `iamcredentials`.
- **`remove_default_node_pool` está deprecado.** El reemplazo (omitir `initial_node_count`) pide GKE ≥ `1.36.4-gke.1469000`. Se mantiene hasta conocer la versión del cluster.
- **Plan Free de Neon** (doc del 2026-11-11):
  - 100 projects, 10 branches y 1 GB por project (20 GB en total), 100 CU-horas y 5 GB de egress por project;
  - scale to zero fijo en 5 minutos;
  - historia de 6 horas;
  - IP Allow y Private Networking solo en Scale.
  - El ADR-0011 decía 0,5 GB y 5 projects.
- **Módulo `neon`:**
  - un `neon_project` por servicio con `for_each`, porque las cuotas son por project; la branch `main` y el role owner se nombran en el bloque `branch`;
  - las bases se llaman igual que en las URLs de dev: `identity_service_db`, `catalog_service_db`, `properties`, `analytics` y `keycloak`;
  - `history_retention_seconds = 21600`, porque el default del provider (1 día) falla en Free;
  - provider `kislerdm/neon ~> 0.18`. `neondatabase/neon` salió en beta el 2026-11-11 y se migraría con `state replace-provider`;
  - las URIs con credenciales salen como output sensitive, para llevarlas a Secret Manager. Quedan en el state.
- **Front en Cloudflare Pages**, como dice el ADR-0015; Workers queda para después.
  - El proyecto no tiene fuente de Git: el CI corre lint y tests y después `wrangler pages deploy`. Wrangler es la CLI que llama el CI; la que se salta el CI es la integración con Git.
  - Terraform crea el proyecto, el dominio `app.` y el CNAME.
- **Módulo `cloudflare/r2`:**
  - los 4 buckets de dev;
  - públicos `property-images` en `img.` (TTL de 30 días en el edge y 7 días en el navegador) y `profile-photos` en `avatars.` (1 hora y 5 minutos, porque la key de la foto se sobrescribe);
  - privados `properties` y `mlflow-artifacts`;
  - CORS de `PUT` y `GET` desde `app.` en los buckets que reciben subidas del navegador;
  - `location = enam`, porque R2 no tiene región en Sudamérica.
- **Por qué dos buckets públicos y subdominios de un nivel.** Los tokens de R2 se limitan por bucket, no por prefijo, así que un solo bucket rompería el mínimo privilegio. Y Universal SSL solo cubre `*.<dominio>`: `x.cdn.<dominio>` necesitaría Advanced Certificate Manager. Con custom domain el bucket no va en la ruta, así que `build_public_url` tiene que armar `{base}/{key}`.
- **Zero Trust Access** delante de `api.<dominio>/v1/admin/*`, con los correos de `admin_emails` puestos en el `terraform.tfvars` local, nunca en el repo:
  - **solo la API:** la ruta `/admin` del SPA navega en el cliente y nunca pasaría por Access;
  - **preflight:** `options_preflight_bypass` deja que el CORS de FastAPI responda; no se puede combinar con `cors_headers`;
  - **cookie:** `HttpOnly` y `SameSite=Lax`; como `app.` y `api.` son el mismo sitio, viaja en los `fetch`;
  - **login:** hay que iniciar sesión una vez abriendo el host `api.`.
- **WAF por IP:** una VPN con IP fija permitiría una regla del tipo `/v1/admin` desde esa IP, pero se eligió Access, que filtra por identidad y es gratis hasta 50 usuarios.
- **Key de Maps (`google_apikeys_key`):**
  - es una key nueva, porque la vieja está en el historial de git y hay que rotarla;
  - restringida a `https://app.<dominio>/*` y a `maps-backend` y `places`, que es lo que carga el front;
  - output sensitive para el secret `VUE_APP_GMAPS_KEY`.
- **Una zona admite un solo ruleset por fase:** las reglas de caché futuras van en el `cloudflare_ruleset` de `r2`.

## Open questions
- Dominio (pendiente del rebrand): está como variable `domain` / `cloudflare_zone_id`.
- Región de GKE y Neon (São Paulo o Virginia).
- Si R2 soporta las escrituras condicionales que necesita `use_lockfile` para el lock del state.
- Role `app` de Neon con solo permisos de DML: los `GRANT` no los maneja la API de Neon.

## Next steps
- Cloudflare, pendiente: tunnel, TLS de la zona (Full strict, HSTS, TLS 1.2), reglas custom del WAF y rate limit, y tokens de R2 por bucket hacia Secret Manager.
- Bootstrap de Argo en su propio stack (ya en `open-items`).
- Backend del state en R2 cuando exista el bucket.
- `terraform` y `gcloud` en el devcontainer.
- Back: que `build_public_url` omita el bucket con custom domain; key de la foto de perfil versionada para poder cachearla largo.
- Corregir en la wiki los límites de Neon (ADR-0011 y `open-items`).
