---
title: Dependencias de plataforma en k8s (infra self-host)
status: draft
last-verified: 2026-07-31
owners: [_shared]
related:
  - "[[deployment-k8s-helm]]"
  - "[[adr-cilium-cni-gateway]]"
  - "[[adr-auth-keycloak-jwt]]"
  - "[[architecture]]"
  - "[[open-items]]"
sources: [../../sources/_shared/2026-07-31-k8s-selfhost-infra-design.md]
---

## TL;DR

Cómo se despliegan las dependencias de plataforma (Keycloak, Redis, MinIO, Kafka, MLflow, ORS) en el cluster self-host. A diferencia de los microservicios (chart Helm genérico, ver [[deployment-k8s-helm]]), las deps son **singletons** → van como **manifiestos planos** en `k8s/infra/<dep>/`, salvo lo que justifica un operador. Estado 2026-07-31: escritos Keycloak y Redis; nada desplegado aún. `draft`.

## Por qué manifiestos planos (no Helm)

El chart genérico existe porque hay 4 microservicios casi idénticos (payoff de DRY). Las deps de plataforma son **únicas entre sí** (Keycloak ≠ Redis ≠ MinIO) → templatizar cada una sería over-engineering. Van como YAML plano en `k8s/infra/<dep>/`. Para el eje multi-entorno self-host (dev/prod con distinta config), el plan es **Kustomize** (base plana + overlays), no Helm — retoma el plan original CNPG + Kustomize. El mix Helm (microservicios) + Kustomize (infra) es deliberado: cada herramienta donde brilla.

## Operadores vs plano

Solo **CloudNativePG** y **Strimzi (Kafka)** van como operador (instalados por Helm con `--wait` en `k8s/scripts/02-plataforma.sh`); el resto plano. Regla: operador solo cuando el día-2 (upgrades/failover/topics) justifica el CRD extra. Para Kafka, Strimzi aporta CRs `Kafka` + `KafkaTopic` (reemplazan el `topic-init` del docker-compose). Keycloak, Redis, MinIO, MLflow y ORS no cumplen ese umbral hoy.

## Keycloak — aislado en su propio namespace

Keycloak es el pilar de auth (ver [[adr-auth-keycloak-jwt]]) y se aísla en el namespace **`identity`** con su propia BD, para poder cerrarlo con NetworkPolicies. Manifiestos en `k8s/infra/keycloak/`:

- `database.yml` — `Cluster` CNPG `keycloak-db` (Postgres plano, sin PostGIS), BD/owner `keycloak`.
- `deployment.yml` — imagen `quay.io/keycloak/keycloak:26.4.7` (paridad con docker-compose), `start-dev --import-realm`, puerto `http` 8080.
- `service.yml` — Service **`keycloak`** (el nombre importa: el DNS `keycloak.identity.svc.cluster.local` depende de él), puerto 8080.
- `config.yml` / `secret.yml` / `realm.yml` — ConfigMap de config no-secreta, Secret de creds admin, ConfigMap del realm montado en `/opt/keycloak/data/import` (pendientes de rellenar).

Al mover Keycloak de `platform` a `identity`, se actualizó el DNS en los 4 values de microservicio (`KEYCLOAK_URL`, `KC_JWKS_URL`) a `keycloak.identity.svc.cluster.local`. El `KC_ISSUER` **no** cambió: es la URL externa del navegador (el claim `iss`), no DNS interno.

### Mapeo de la BD (contratos distintos)

Los microservicios leen una sola `DATABASE_URL` desde la clave `uri` del secret CNPG (contrato Python/SQLAlchemy). Keycloak es distinto: usa 3 env separadas desde el secret `keycloak-db-app`: `KC_DB_URL`←`jdbc-uri` (formato JDBC, `uri` no le sirve), `KC_DB_USERNAME`←`username`, `KC_DB_PASSWORD`←`password`. No lo exige (el `jdbc-uri` embebe creds), pero 3 separadas mantienen el password fuera de la URL → menos fuga en logs.

## Redis — plano, cache

`k8s/infra/redis/` con Deployment + Service. Corre con `--maxmemory 1200mb --maxmemory-policy allkeys-lru`: al llenar el límite de memoria, Redis evicciona LRU en vez de que k8s haga OOMKill al pod (comportamiento correcto de cache). Sin persistencia (es cache).

## Config vs secretos

Config no-secreta → inline en el manifiesto plano (dev). Secretos → siempre recurso `Secret` (dummy en dev, real por Sealed Secrets/ESO en prod), referenciados por el Deployment, **nunca inline en `env:`**. Así el Deployment no cambia entre dev y prod, solo la fuente del Secret. La conexión a BD nunca se hardcodea: sale del secret `<cluster>-app` que genera CNPG.

## Los tres planos de seguridad (aclaración)

No confundir: **NetworkPolicy** (L3/4, quién manda paquetes) ≠ **RBAC de k8s** (quién llama a la API de k8s) ≠ **OIDC/Keycloak** (auth de app). Los pods de app no necesitan tocar la API de k8s → KSA sin RoleBindings + `automountServiceAccountToken: false`. Cerrar el UI admin de Keycloak es NetworkPolicy (no publicar `/admin` por el Gateway) + el login admin propio, no RBAC de k8s.

## ORS — bloqueado

ORS (`k8s/infra/ors/`) resultó el más tramposo de los "fáciles": el seed `.osm.pbf` y el grafo construido **no están en el repo** (solo `infra/ors/config/`). El grafo es artefacto build-once (cache): ORS lo construye del `.pbf` la 1ª vez y lo reusa; conviene persistir el grafo construido (PVC + backup en MinIO) en vez de reconstruir por entorno. Es la dep pesada (~6GB de heap). Bloqueado hasta re-conseguir el `.pbf` — ver [[open-items]].

## Claims

- Las deps de plataforma viven como manifiestos planos en `k8s/infra/<dep>/`, una carpeta por dependencia (keycloak, kafka, redis, minio, mlflow, ors).
- Solo CloudNativePG y Strimzi se instalan como operadores (por Helm en `k8s/scripts/02-plataforma.sh`); el resto es plano.
- `k8s/bootstrap/namespaces.yml` incluye el namespace `identity`, donde vive Keycloak y su BD.
- El Deployment de Keycloak usa la imagen `quay.io/keycloak/keycloak:26.4.7` y mapea `KC_DB_URL`/`KC_DB_USERNAME`/`KC_DB_PASSWORD` desde las claves `jdbc-uri`/`username`/`password` del secret `keycloak-db-app`.
- El Service de Keycloak se llama `keycloak`; los 4 values de microservicio apuntan a `keycloak.identity.svc.cluster.local` en `KEYCLOAK_URL`/`KC_JWKS_URL`.
- El Deployment de Redis corre con `--maxmemory-policy allkeys-lru` para evictar en vez de morir por OOMKill.