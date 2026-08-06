---
title: Despliegue k8s self-host — chart Helm de microservicio
status: draft
last-verified: 2026-07-31
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[project-roadmap-2026]]"
  - "[[open-items]]"
  - "[[users-service]]"
  - "[[platform-deps-k8s]]"
  - "[[adr-cilium-cni-gateway]]"
sources:
  - ../../sources/_shared/2026-07-29-k8s-helm-microservice-chart.md
  - ../../sources/_shared/2026-07-31-k8s-selfhost-infra-design.md
---

## TL;DR

Track paralelo (modo aprendizaje) para desplegar el monorepo en Kubernetes self-hosted. Un **chart Helm genérico** (`k8s/charts/microservice/`) modela un microservicio y se reusa para los 4 (users/catalog/properties/analytics) vía `values/<ms>.yaml`. Postgres se auto-gestiona con **CloudNativePG** (un `Cluster` por servicio). Estado 2026-07-31: chart + scripts de bootstrap (kind/Cilium, operadores) + primeras deps de plataforma escritos, pero **nada desplegado ni verificado** — el PC actual no corre kind ni helm. `draft` hasta que se pruebe con `helm template`/`helm lint` y se despliegue. La capa de deps de plataforma vive en [[platform-deps-k8s]].

## Contexto y decisiones

- **Objetivo**: staging/aprendizaje, NO la infra de la beta. Sin presión de fecha.
- **Self-host** de todo lo stateful (Postgres, Redis, MinIO, Kafka) como pods — no managed GCP.
- **Herramienta**: se arrancó en Kustomize (para aprender los recursos crudos) y se **pivotó a Helm**. Razón: N microservicios casi idénticos = el eje paramétrico de Helm (un molde + values por servicio); Kustomize es el eje "1 app × N entornos". Kustomize se removió; se puede recombinar (`helmCharts` + `--enable-helm`) solo si un parche lo requiere.
- **Cluster**: kind local primero (gratis, mismo YAML), **k3s** después para el self-host real (migración barata: la capa de app es portable, solo se reescribe el bootstrap). La red la resuelve **Cilium** como CNI unificado (CNI + NetworkPolicies + Gateway API), decidido tras el retiro de ingress-nginx — ver [[adr-cilium-cni-gateway]]. En kind eso implica `disableDefaultCNI: true` + `kubeProxyMode: "none"`.

## Postgres — CloudNativePG

- **Un `Cluster` por servicio** (patrón DB-por-servicio, preserva aislamiento). `instances` = pods réplica (HA), no bases de datos.
- `catalog` y `properties` usan imagen **PostGIS** (`imageName`); `users`/`analytics` la estándar.
- El operator **auto-genera** un secret `<cluster>-app` (claves `uri`, `host`, `username`, `password`, `dbname`, …). La app lee `DATABASE_URL` de la clave `uri` — nunca se escribe a mano.
- Servicios que crea: `-rw` (primary, sigue el failover), `-ro` (réplicas), `-r` (cualquiera).
- El schema lo posee **Alembic** (migraciones), no el init SQL de cnpg — evita dos fuentes de verdad.

## Migraciones y orden de arranque

- Kubernetes no tiene `depends_on`; converge por reintentos. El orden se fuerza con initContainers, readiness probes, o (con Helm/Argo) hooks/sync-waves.
- El **Job** de migración corre `alembic upgrade head` y es un **Helm hook** `post-install,pre-upgrade` (+ `hook-delete-policy: before-hook-creation`). Es `post-install` y **no** `pre-install` porque el `Cluster` de CNPG (recurso normal) no existe todavía en el install; el `hook-delete-policy` evita el fallo del 2º upgrade por la inmutabilidad del Job.
- En **upgrade**, el hook `pre-upgrade` corre a completitud antes de aplicar el Deployment → orden estricto migración→app. En **install**, el hook `post-install` corre *después* del Deployment, así que el orden lo sostiene el initContainer **`wait-for-migration`** del Deployment, que **espera a que el schema iguale a head (`alembic current == heads`), no solo a que la DB responda** — si no, el Service enruta tráfico a pods sin migrar. El initContainer del Job solo espera la DB (`pg_isready`).
- El Job de migración necesita **solo `DATABASE_URL`**: `env.py` de Alembic importa `app.models.*` (sqlmodel), que no importan `settings`, así que no requiere el `envFrom` de config completa.

## Config, secretos y labels (patrones Helm)

- Labels estándar `app.kubernetes.io/*` vía `_helpers.tpl`; cada recurso añade `app.kubernetes.io/component` (backend/database/migration). El **selector usa solo `selectorLabels` (name+instance)** — el subconjunto mínimo e inmutable; los labels completos (con version/env/component) van en metadata + pod template.
- Anotación **`checksum/config`** (sha256 del configmap renderizado) en el pod template → rollout automático cuando cambia la config (k8s no reinicia pods al cambiar un ConfigMap).
- ConfigMap y Secrets se generan con `range` sobre mapas en values (`config`, `secretData`).
- **Secretos**: base64 ≠ cifrado; nunca se commitean valores reales. Los dummy van tras el flag `createDummySecrets`; los reales llegan por Sealed Secrets → Vault dev + ESO (fase de seguridad). El chart **referencia** secrets por nombre (`envFrom`), no gestiona los reales.
- **Namespaces**: fuente única en `k8s/bootstrap/namespaces.yml` (aplicado con `kubectl apply` en la fase de plataforma); el `helm install` usa `-n <ns>` **sin** `--create-namespace`, y los templates **no** hardcodean `namespace` (lo pone `helm -n`). Uno por microservicio (`<ms>-ms`) + `platform` + `identity` (Keycloak aislado, ver [[platform-deps-k8s]]). *(Antes se usaba `--create-namespace`; se cambió para tener una sola fuente de namespaces con labels consistentes.)*
- **Sin ServiceAccount/RBAC custom** — ningún workload llama a la API de k8s; el pod usa la SA `default`. Hardening opcional diferido: SA dedicada con `automountServiceAccountToken: false`. El operator cnpg trae su propio RBAC.

## Operadores y scripts de bootstrap

- Solo **CloudNativePG** y **Strimzi (Kafka)** se instalan como operadores (por Helm, con `--wait`); el resto de la plataforma va como manifiestos planos (ver [[platform-deps-k8s]]). Regla: operador solo cuando el día-2 (upgrades/failover/topics) justifica el CRD extra.
- El bootstrap del cluster vive en `k8s/install.sh` (orquestador: mapa fase→script, sin lógica) + `k8s/scripts/NN-*.sh` (una fase cada uno) + `k8s/scripts/lib.sh` (helpers + wrappers `kc`/`h` que pinnean `--context`/`--kube-context` a `kind-<cluster>`, para no instalar en el cluster equivocado). Instalaciones idempotentes (`helm upgrade --install`, guards de existencia).

## Pendiente

Ver [[project-roadmap-2026]] Fase 4 y [[open-items]]. Próximos pasos: `helm lint`/`helm template` (cuando haya máquina con helm), instalar el operator cnpg, `values/<ms>.yaml` por servicio, chart/instalación de `platform`, y la fase de seguridad (NetworkPolicies + CNI, Sealed Secrets/ESO, SA hardening, HPA).

## Claims

- El chart genérico vive en `k8s/charts/microservice/` y modela un microservicio reutilizable vía values por servicio.
- El Postgres de cada servicio es un `Cluster` de CloudNativePG llamado `<app.name>-cluster`; el Deployment lee `DATABASE_URL` de la clave `uri` del secret `<app.name>-cluster-app` que genera el operator.
- El `Job` de migración corre `alembic upgrade head` como Helm hook `post-install,pre-upgrade` con `hook-delete-policy: before-hook-creation`; el initContainer `wait-for-migration` del Deployment bloquea hasta que el schema iguala a head, no solo hasta que la DB responde.
- Los secrets dummy se crean solo si `.Values.createDummySecrets` es true; el chart referencia secrets por nombre vía `envFrom` y no gestiona los reales.
- El Deployment lleva una anotación `checksum/config` con el sha256 del configmap renderizado para forzar rollout al cambiar la config.
- Los namespaces se crean aplicando `k8s/bootstrap/namespaces.yml`; el `helm install` usa `-n <ns>` sin `--create-namespace`.
- El `kind/config.yml` declara `disableDefaultCNI: true` y `kubeProxyMode: "none"` para que Cilium sea el CNI con `kubeProxyReplacement`.