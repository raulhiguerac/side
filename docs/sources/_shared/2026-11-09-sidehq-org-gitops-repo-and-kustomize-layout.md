---
title: Org sidehq, repo de GitOps aparte y layout con Kustomize + ApplicationSets
captured-from: conversation
captured-on: 2026-11-09
participants: [author, claude]
---

## Context
Con el MVP de código cerrado por ahora (change-password y reactivación en #41), el autor pasó a la infra de la demo pública. Se decidió separar el despliegue en su propio repo para que Argo CD haga el CD, y se revisó lo que ya existía: la rama `infra/k8s` de agosto y el Terraform de GKE del proyecto `pde`.

## Key conclusions
- **Repos.**
  - El monorepo pasó de `raulhiguerac/side` a la org **`sidehq`** como **`sidehq/app`**. El ruleset de `main` viajó con el repo.
  - Se creó **`sidehq/infra`** (público) para GitOps, con SonarCloud configurado (`build.yml` + `sonar-project.properties`, key `sidehq_infra`).
  - `sidehq` es un nombre provisional: `side` está tomado y viene un rebrand corto. Hay que renombrar la org **antes** de cablear GHCR, workflows reutilizables o el `repoURL` de Argo, porque esos no se redirigen.
- **Merges.** #39 se había mergeado sobre `refactor/users-api-layout` y no sobre `main`. Se corrigió cambiando la base de #40 a `main`, que entró con sus 6 commits. Con la org nueva, el ruleset tiene `bypass_actors: []`, así que `--admin` puede dejar de funcionar.
- **Clone local de infra.** Está en `side/gitops/` (`side/infra/` ya existe con las deps del compose), excluido con `.git/info/exclude`. En el devcontainer se ve en `/workspace/gitops`.
- **CD de imágenes.** El CI de `app` construye, publica y escribe el **digest** en `infra`; Argo sincroniza. Dependabot no sirve como CD porque corre por calendario y abre un PR por cambio. Dependabot o Renovate quedan para fijar por digest las imágenes base y mantener las deps al día.
- **Rama `infra/k8s`.** Su `k8s/` pasó tal cual a `infra` con `git subtree split`: 4 commits, sin el de docs. Tenía bugs respecto al código de hoy:
  - el chart inyecta siempre `DATABASE_URL`, pero catalog, properties y analytics leen `DATABASE_<SVC>_URL`;
  - users sigue con el secret de Brevo en vez de SMTP;
  - properties usa `AWS_*` en vez de `ACCESS_KEY_PROPERTIES` / `SECRET_KEY_PROPERTIES`;
  - la base de datos va en CNPG, que contradice [[adr-stateless-cluster-external-data]].
- **Kustomize en vez del chart genérico.** Se quita el chart de Helm:
  - `templates/microservice` es la base de Kustomize;
  - `services/<ms>` es un overlay por servicio con `configMapGenerator` e `images` (con digest);
  - un ApplicationSet con generador de directorios crea una app por servicio;
  - la migración es un Job con hook `PreSync` de Argo.
- **Config y secretos.**
  - `configMapGenerator` arma el ConfigMap al hacer el build, con un hash en el nombre, así que los pods se reinician si la config cambia. No puede leer Secrets del cluster: el pod junta las dos fuentes con `envFrom`.
  - La config compartida no secreta (JWKS, issuer, audience, Redis) va en `shared/platform.env`, versionada en git.
  - Los secretos van por ESO: un `SecretStore` por namespace, y `ClusterSecretStore` + `ClusterExternalSecret` solo para secretos que de verdad sean compartidos.
- **Tree de infra** (commit `f89bf37`, con archivos vacíos para dejar registro de cómo empezó):
  - `argo/{root-app,projects,applicationsets}`, `templates/microservice`, `services/{users,catalog,properties,analytics}` y `shared/`;
  - `platform/{namespaces,keycloak,redis,kafka,ors,external-secrets,cloudflared}`;
  - `terraform/{gke,neon,r2,cloudflare}`;
  - `local/` con kind y los scripts.
  - Salieron `charts/`, los `database.yml` de CNPG, `minio/` y `mlflow/`.
- **GKE.** Standard **zonal**, reusando el módulo de `pde`: VPC, subnet con rangos secundarios, Workload Identity, node pool aparte, Argo y ESO por Helm, y KSA↔GSA para ESO contra Secret Manager. Autopilot se descarta porque es regional y cobra por los requests de cada pod.
- **Bugs del módulo de `pde` a corregir al traerlo:**
  - el rango de services `192.170.10.0/24` no es RFC1918;
  - los `source` `./modules/Buckets` y `./modules/Kubernetes` tienen mayúsculas que no coinciden con las carpetas y fallan en Linux;
  - `google 5.13.0` y `google-beta ~>4` están en majors distintos;
  - `gavinbunney/kubectl` está sin mantenimiento.
- **Ajustes de diseño al módulo:**
  - separar el cluster del bootstrap de Argo en dos stacks;
  - usar ADC o Workload Identity Federation en vez de una key JSON;
  - nodos `spot` chicos (1–2 `e2-standard-2`) en vez de 6 `n1-standard-2`;
  - `secretAccessor` en vez de `secretmanager.admin` para ESO;
  - fuera `repository` (`docker build` con `local-exec`), Cloud SQL, buckets y secrets de Airflow.

## Open questions
- Si el crédito de GCP aplica (no aplica si ya fuiste cliente de pago de Maps Platform). Decide el destino del cluster.
- Backend de ESO: GCP Secret Manager (ya probado en `pde`, pero se va con el crédito el día 91) o uno neutral.
- Qué pasa con `local/` (kind + Cilium): ¿se mantiene como cluster local o se borra? `02-plataforma.sh` todavía instala CNPG y Strimzi y apunta a `bootstrap/namespaces.yml`, que ya no existe.
- Nodos públicos con firewall cerrado o privados con Cloud NAT.

## Next steps
- Traer el módulo de `pde` a `terraform/gke/` con los arreglos (red + cluster) y, como segundo paso, el bootstrap de Argo.
- Llenar `templates/microservice` y `services/users` con contenido real.
- En `app`:
  - volver a enlazar SonarCloud a la org;
  - corregir la URL de clone en `README.md`;
  - agregar Repository admin como bypass del ruleset si `--admin` falla.
- Primera versión recortada: sin Kafka ni el consumer de analytics, ORS solo si catalog lo necesita para arrancar, Terraform de Cloudflare y Neon después de hacerlos a mano.
