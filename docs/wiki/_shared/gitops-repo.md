---
title: Repo de GitOps (sidehq/infra)
status: draft
last-verified: 2026-11-11
owners: [_shared]
related:
  - "[[adr-kustomize-applicationsets-gitops]]"
  - "[[adr-stateless-cluster-external-data]]"
  - "[[project-roadmap-2026]]"
  - "[[open-items]]"
  - "[[dev-workflow]]"
sources:
  - ../../sources/_shared/2026-11-09-sidehq-org-gitops-repo-and-kustomize-layout.md
  - ../../sources/_shared/2026-11-11-terraform-gke-neon-cloudflare-modules.md
---

# Repo de GitOps (sidehq/infra)

## TL;DR

Lo que se despliega vive en `sidehq/infra` (público), separado del código en `sidehq/app`. Argo CD lee solo ese repo. El CI de `app` construye las imágenes y escribe su digest ahí. Responde dónde está cada pieza del despliegue y cómo llega un cambio al cluster.

## Contenido

### Repos y nombres

- El 2026-11-09 el monorepo pasó de `raulhiguerac/side` a **`sidehq/app`**, y se creó **`sidehq/infra`**.
- `sidehq` es un nombre provisional porque viene un rebrand. La org se renombra **antes** de cablear GHCR, workflows reutilizables o el `repoURL` de Argo, porque esas referencias no se redirigen.
- En local, `infra` se clona en `side/gitops/` (`side/infra/` ya existe con las deps del compose). Está excluido con `.git/info/exclude` de `app` y en el devcontainer aparece en `/workspace/gitops`, porque el compose monta `side/` entero. Cada carpeta tiene su propio `.git`.
- `infra` tiene SonarCloud con `build.yml` y `sonar-project.properties` (key `sidehq_infra`).

### Layout

Sembrado vacío el 2026-11-09 para dejar registro de cómo empezó ([[adr-kustomize-applicationsets-gitops]]):

```
argo/          root-app.yaml (app-of-apps) · projects/ · applicationsets/{microservices,platform}.yaml
templates/microservice/   base de Kustomize: deployment, service, migration-job (PreSync)
services/<ms>/            kustomization.yaml · config.env · external-secret.yaml
shared/platform.env       config compartida no secreta (JWKS, issuer, audience, Redis)
platform/                 namespaces · keycloak · redis · kafka · ors · external-secrets · cloudflared
terraform/                raíz única: gke · neon · cloudflare (r2, front, access) · maps
local/                    kind + scripts de la rama infra/k8s (pendiente de decidir)
```

La rama `infra/k8s` de `app` se trajo con `git subtree split` (4 commits) y luego se reorganizó. Salieron el chart, CNPG, MinIO y MLflow, por [[adr-stateless-cluster-external-data]].

### Cómo llega un cambio al cluster

1. Merge a `main` en `app` → el CI construye la imagen y la publica.
2. El CI hace commit en `infra` con el digest nuevo en `services/<ms>/kustomization.yaml`.
3. Argo detecta el commit y sincroniza. La migración corre como hook `PreSync` antes de que roten los pods.

Dependabot (o Renovate) no forma parte del CD: solo fija por digest las imágenes upstream (Keycloak, Redis, cloudflared) y mantiene al día las deps.

### Config y secretos

- **Config no secreta:** `configMapGenerator` la arma al hacer el build, con un hash en el nombre. Si la config cambia, los pods se reinician.
- **Secretos:** External Secrets Operator, con un `SecretStore` por namespace para que cada servicio solo lea lo suyo. `ClusterSecretStore` + `ClusterExternalSecret` solo para secretos que de verdad sean compartidos.
- **Cómo se juntan:** el pod une las dos fuentes con `envFrom`. `configMapGenerator` no puede leer Secrets del cluster.

El backend de ESO está sin decidir: GCP Secret Manager ya está probado en `pde`, pero se va con el crédito el día 91.

### Cluster

GKE Standard **zonal**, reusando el módulo de Terraform del proyecto `pde`: VPC, subnet con rangos secundarios, Workload Identity, node pool aparte y el binding KSA↔GSA para ESO. Autopilot se descartó porque es regional y cobra por los requests de cada pod. Los arreglos pendientes del módulo están en [[open-items]], sección "Despliegue k8s (`sidehq/infra`)".

### Terraform

Desde el 2026-11-11 está escrito y validado con `terraform validate` en el contenedor `hashicorp/terraform:1.17.2`, porque el devcontainer no tiene `terraform` ni `gcloud`. Todavía no se aplicó.

- **Una raíz en `terraform/`**, con un solo `init` y un solo state. Los providers se configuran solo ahí:
  - `google` por ADC, sin key JSON;
  - `neon` por `NEON_API_KEY`;
  - `cloudflare` por `CLOUDFLARE_API_TOKEN`.
  Los módulos solo declaran `required_providers`. Los valores van en `terraform.tfvars`, ignorado por git; el `.example` es público.
- **State:** el bucket de R2 que lo guarda se crea a mano, fuera de Terraform, con un token limitado a ese bucket. Hasta entonces el state es local.
- **`gke`** (adaptado de `pde`, sin Cloud SQL ni Airflow): submódulos `services`, `network`, `cluster` e `identity`.
  - CIDR: nodos `10.10.0.0/24`, pods `10.20.0.0/20` y services `10.30.0.0/22`.
  - 64 pods por nodo, que en GKE es un /25 por nodo.
  - Nodos `spot` con una cuenta propia (`roles/container.defaultNodeServiceAccount`).
  - Workload Identity con `GKE_METADATA`: solo la KSA de ESO tiene binding a una GSA, con `secretAccessor`.
- **`neon`:** un `neon_project` por servicio, porque las cuotas del plan Free son por project.
  - Las bases se llaman como en dev y la branch es `main`.
  - `history_retention_seconds = 21600`, porque el plan Free solo guarda 6 horas.
  - Las URIs con credenciales salen como output sensitive y quedan en el state.
- **`cloudflare/r2`:** los 4 buckets de dev.
  - Públicos: `img.` con TTL largo, porque las keys tienen UUID, y `avatars.` con TTL corto, porque la foto se sobrescribe en la misma key.
  - CORS de `PUT` desde `app.` donde el navegador sube con URL presignada.
  - Un solo `cloudflare_ruleset` de caché, porque la zona admite uno por fase.
- **`cloudflare/front`:** proyecto de Pages sin fuente de Git, con el dominio `app.` y su CNAME. El CI corre lint y tests y después `wrangler pages deploy`.
- **`cloudflare/access`:** Zero Trust Access solo delante de `api.<dominio>/v1/admin/*`. La ruta `/admin` del SPA navega en el cliente y nunca pasaría por Access.
  - `options_preflight_bypass` deja que el CORS de FastAPI responda el preflight.
  - La cookie es `HttpOnly` y `SameSite=Lax`, y como `app.` y `api.` son el mismo sitio, viaja sola en los `fetch`.
- **`maps`:** una key nueva de Maps, restringida a `https://app.<dominio>/*` y a `maps-backend` y `places`. La vieja está en el historial de git y hay que rotarla.

## Claims

- La rama `infra/k8s` sigue existiendo en `sidehq/app` con el chart genérico en `k8s/charts/microservice/` (`git show origin/infra/k8s:k8s/charts/microservice/Chart.yaml`).
- El servicio `develop` del compose monta la raíz del repo en `/workspace` ([docker-compose.yml](docker-compose.yml)).
