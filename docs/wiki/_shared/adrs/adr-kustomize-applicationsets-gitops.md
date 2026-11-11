---
title: ADR-0016 — Kustomize + ApplicationSets en un repo de GitOps aparte, en lugar del chart genérico de Helm
status: stable
last-verified: 2026-11-09
owners: [_shared]
related:
  - "[[gitops-repo]]"
  - "[[adr-stateless-cluster-external-data]]"
  - "[[project-roadmap-2026]]"
  - "[[open-items]]"
sources:
  - ../../../sources/_shared/2026-11-09-sidehq-org-gitops-repo-and-kustomize-layout.md
decision-date: 2026-11-09
decision-status: accepted
---

# ADR-0016 — Kustomize + ApplicationSets en un repo de GitOps aparte, en lugar del chart genérico de Helm

## Contexto

La rama `infra/k8s` (agosto de 2026) tenía un chart de Helm genérico para los 4 servicios, con values por servicio, CNPG para las bases y la migración como hook de Helm. Después se decidió un cluster sin estado ([[adr-stateless-cluster-external-data]]) con Argo CD como CD. Además, la config de los servicios cambió y el chart se quedó atrás: inyectaba siempre `DATABASE_URL`, cuando tres servicios leen `DATABASE_<SVC>_URL`.

## Decisión

Los manifiestos viven en `sidehq/infra`, separados del código. Tienen una base de Kustomize (`templates/microservice`), un overlay por servicio (`services/<ms>`) y un ApplicationSet con generador de directorios que crea una app de Argo por servicio.

- **Config no secreta:** sale de `configMapGenerator`, con `shared/platform.env` para lo común más el `config.env` de cada servicio.
- **Secretos:** llegan por External Secrets Operator.
- **Imagen:** se fija por digest en `images:`; el CI de `app` solo cambia esa línea.
- **Migración:** es un Job con `argocd.argoproj.io/hook: PreSync`.

## Alternativas consideradas

- **Mantener el chart genérico de Helm.** Templating para cuatro servicios casi iguales, y los hooks de Helm se traducen mal en Argo: `post-install,pre-upgrade` corre dos veces por sync. El `checksum/config` que el chart usaba para reiniciar pods ya lo hace `configMapGenerator` con el hash del nombre.
- **Config dentro del ApplicationSet** (`kustomize.patches` o un generador de lista con parámetros). La config de los 4 servicios quedaría en un solo YAML grande, y el bump de la imagen editaría ese archivo compartido.
- **Manifiestos en el monorepo de `app`.** Los commits de bump ensuciarían `main` y dispararían el CI de la app, y Argo tendría acceso de lectura a todo el código.
- **Dependabot para promover las imágenes propias.** Corre por calendario (diario como mucho) y abre un PR por cambio. Queda solo para fijar por digest las imágenes base y mantener las deps al día.

## Consecuencias

- ✅ El CD es un commit de una línea (`kustomize edit set image …@sha256:…`) que Argo sincroniza solo.
- ✅ Un cambio de config cambia el nombre del ConfigMap y reinicia los pods, sin templating.
- ✅ La config no secreta queda versionada en git; los secretos no tocan el repo, que es público.
- ❌ `configMapGenerator` no puede leer Secrets del cluster: el pod junta ConfigMap y Secret con `envFrom`.
- ❌ Una clave repetida entre `shared/platform.env` y el `config.env` de un servicio hace fallar el build. Un override necesita un component o `behavior: merge`.
- ❌ Cada cambio de config deja ConfigMaps huérfanos. Las apps necesitan `prune` con `PruneLast=true`.
- ❌ El CI de `app` necesita permiso de escritura sobre `sidehq/infra` (una GitHub App o un PAT fine-grained).

## Claims

- La rama `infra/k8s` de `sidehq/app` todavía contiene el chart genérico en `k8s/charts/microservice/` (`git show origin/infra/k8s:k8s/charts/microservice/Chart.yaml`).
- catalog, properties y analytics leen la base desde `DATABASE_CATALOG_URL`, `DATABASE_PROPERTIES_URL` y `DATABASE_ANALYTICS_URL` ([catalog .env.dev](backend/catalog-service/.env.dev), [properties .env.dev](backend/properties-service/.env.dev), [analytics .env.dev](backend/analytics-service/.env.dev)).
