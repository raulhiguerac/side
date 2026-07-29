---
title: Despliegue k8s self-host — chart Helm de microservicio
status: draft
last-verified: 2026-07-29
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[project-roadmap-2026]]"
  - "[[open-items]]"
  - "[[users-service]]"
sources: [../../sources/_shared/2026-07-29-k8s-helm-microservice-chart.md]
---

## TL;DR

Track paralelo (modo aprendizaje) para desplegar el monorepo en Kubernetes self-hosted. Un **chart Helm genérico** (`k8s/charts/microservice/`) modela un microservicio y se reusa para los 4 (users/catalog/properties/analytics) vía `values/<ms>.yaml`. Postgres se auto-gestiona con **CloudNativePG** (un `Cluster` por servicio). Estado 2026-07-29: chart escrito pero **nada desplegado ni verificado** — el PC actual no corre kind ni helm. `draft` hasta que se pruebe con `helm template`/`helm lint` y se despliegue.

## Contexto y decisiones

- **Objetivo**: staging/aprendizaje, NO la infra de la beta. Sin presión de fecha.
- **Self-host** de todo lo stateful (Postgres, Redis, MinIO, Kafka) como pods — no managed GCP.
- **Herramienta**: se arrancó en Kustomize (para aprender los recursos crudos) y se **pivotó a Helm**. Razón: N microservicios casi idénticos = el eje paramétrico de Helm (un molde + values por servicio); Kustomize es el eje "1 app × N entornos". Kustomize se removió; se puede recombinar (`helmCharts` + `--enable-helm`) solo si un parche lo requiere.
- **Cluster**: kind local primero (gratis, mismo YAML), GKE después. kindnet **no** aplica NetworkPolicies → requiere CNI Calico/Cilium antes de que las policies hagan algo (ver [[open-items]]).

## Postgres — CloudNativePG

- **Un `Cluster` por servicio** (patrón DB-por-servicio, preserva aislamiento). `instances` = pods réplica (HA), no bases de datos.
- `catalog` y `properties` usan imagen **PostGIS** (`imageName`); `users`/`analytics` la estándar.
- El operator **auto-genera** un secret `<cluster>-app` (claves `uri`, `host`, `username`, `password`, `dbname`, …). La app lee `DATABASE_URL` de la clave `uri` — nunca se escribe a mano.
- Servicios que crea: `-rw` (primary, sigue el failover), `-ro` (réplicas), `-r` (cualquiera).
- El schema lo posee **Alembic** (migraciones), no el init SQL de cnpg — evita dos fuentes de verdad.

## Migraciones y orden de arranque

- Kubernetes no tiene `depends_on`; converge por reintentos. El orden se fuerza con initContainers, readiness probes, o (con Helm/Argo) hooks/sync-waves.
- Patrón: un **Job** corre `alembic upgrade head`; el initContainer del Deployment **espera a que la migración esté aplicada (schema == head), no solo a que la DB responda** — si no, el Service enruta tráfico a pods sin migrar (carrera real). El initContainer del Job solo espera la DB (`pg_isready`).
- El Job de migración necesita **solo `DATABASE_URL`**: `env.py` de Alembic importa `app.models.*` (sqlmodel), que no importan `settings`, así que no requiere el `envFrom` de config completa.

## Config, secretos y labels (patrones Helm)

- Labels estándar `app.kubernetes.io/*` vía `_helpers.tpl`; cada recurso añade `app.kubernetes.io/component` (backend/database/migration). El **selector usa solo `selectorLabels` (name+instance)** — el subconjunto mínimo e inmutable; los labels completos (con version/env/component) van en metadata + pod template.
- Anotación **`checksum/config`** (sha256 del configmap renderizado) en el pod template → rollout automático cuando cambia la config (k8s no reinicia pods al cambiar un ConfigMap).
- ConfigMap y Secrets se generan con `range` sobre mapas en values (`config`, `secretData`).
- **Secretos**: base64 ≠ cifrado; nunca se commitean valores reales. Los dummy van tras el flag `createDummySecrets`; los reales llegan por Sealed Secrets → Vault dev + ESO (fase de seguridad). El chart **referencia** secrets por nombre (`envFrom`), no gestiona los reales.
- **Namespaces** vía `helm --create-namespace`, NO como recurso dentro de `templates/` (anti-patrón: Helm podría borrarlos en `uninstall`). Uno por dominio + `platform`.
- **Sin ServiceAccount/RBAC custom** — ningún workload llama a la API de k8s; el pod usa la SA `default`. Hardening opcional diferido: SA dedicada con `automountServiceAccountToken: false`. El operator cnpg trae su propio RBAC.

## Pendiente

Ver [[project-roadmap-2026]] Fase 4 y [[open-items]]. Próximos pasos: `helm lint`/`helm template` (cuando haya máquina con helm), instalar el operator cnpg, `values/<ms>.yaml` por servicio, chart/instalación de `platform`, y la fase de seguridad (NetworkPolicies + CNI, Sealed Secrets/ESO, SA hardening, HPA).

## Claims

- El chart genérico vive en `k8s/charts/microservice/` y modela un microservicio reutilizable vía values por servicio.
- El Postgres de cada servicio es un `Cluster` de CloudNativePG llamado `<app.name>-cluster`; el Deployment lee `DATABASE_URL` de la clave `uri` del secret `<app.name>-cluster-app` que genera el operator.
- El `Job` de migración corre `alembic upgrade head` y el initContainer del Deployment bloquea hasta que el schema iguala a head, no solo hasta que la DB responde.
- Los secrets dummy se crean solo si `.Values.createDummySecrets` es true; el chart referencia secrets por nombre vía `envFrom` y no gestiona los reales.
- El Deployment lleva una anotación `checksum/config` con el sha256 del configmap renderizado para forzar rollout al cambiar la config.
- Los namespaces se crean con `helm --create-namespace`, no como recurso del chart.