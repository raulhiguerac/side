---
title: k8s self-host — decisiones de infra (Cilium, Helm, operadores, deps de plataforma)
captured-from: conversation
captured-on: 2026-07-31
participants: [raul, claude]
---

## Context
Sesión de diseño del track de infra k8s self-host (modo aprendizaje, kind local → k3s futuro). Se definió el stack de red, el empaquetado de los microservicios, qué va como operador, y cómo desplegar las dependencias de plataforma. Nada se ha ejecutado aún: es diseño validado, no sistema corriendo.

## Key conclusions

### Red / cluster
- **ingress-nginx quedó retirado** (repo archivado marzo 2026; su sucesor InGate también murió). Elegido **Cilium** como CNI porque unifica CNI + NetworkPolicies + Gateway API en una pieza (es la migración que recomienda el CNCF tras el retiro).
- **Gateway API** (`Gateway` + `HTTPRoute`) reemplaza a Ingress; cruce de namespaces con `ReferenceGrant`.
- kind con `disableDefaultCNI: true` + `kubeProxyMode: "none"` — Cilium corre con `kubeProxyReplacement=true`, que exige que kube-proxy no exista.
- Cilium en kind: `k8sServiceHost` = IP del contenedor `<cluster>-control-plane` en la red docker `kind`, puerto `6443` (NO el `localhost:7445` de Talos/KubePrism; eso era config específica de Talos, junto a securityContext.capabilities y cgroup).
- Migración kind→k3s es barata: la capa de app es portable; solo se reescribe el bootstrap (k3s: `--flannel-backend=none`, `--disable-network-policy`, `--disable-kube-proxy`, `--disable traefik`). k3s trae LoadBalancer real (Klipper) → sin el hack de `extraPortMappings`.

### Empaquetado de microservicios (Helm)
- Chart genérico + values por servicio (DRY para 4 MS casi idénticos). Las deps de infra NO se templatizan (son singletons, sin payoff DRY) → manifiestos planos.
- Migración como **Helm hook** `post-install,pre-upgrade` + `hook-delete-policy: before-hook-creation`. Es `post-install` y no `pre-install` porque el Cluster CNPG no existe aún en el install. El initContainer `wait-for-migration` sigue siendo necesario en el camino de install (el hook post-install corre después del Deployment; el hook solo garantiza orden estricto en upgrade).
- Namespaces: `bootstrap/namespaces.yml` es fuente única; `helm -n <ns>` SIN `--create-namespace`; los templates no llevan `namespace` hardcodeado (lo pone `helm -n`).

### Operadores y deps de plataforma
- Solo **CNPG** y **Strimzi (Kafka)** como operadores (instalados por Helm, `--wait`); el resto plano (Keycloak, Redis, MinIO, MLflow, ORS). Regla: operador solo cuando el día-2 (upgrades/failover/topics) duele lo suficiente para pagar el CRD extra.
- Keycloak aislado en namespace **`identity`** con su propia BD CNPG (`keycloak-db`). DNS actualizado en los 4 values a `keycloak.identity.svc.cluster.local` (el `KC_ISSUER` NO cambia: es la URL externa del navegador). Realm vía ConfigMap montado en `/opt/keycloak/data/import` + `--import-realm`. El operador de Keycloak se descartó: no trae BD embebida (igual necesitas Postgres).
- Redis: Deployment + Service planos, con `--maxmemory 1200mb --maxmemory-policy allkeys-lru` para evictar en vez de morir por OOMKill al llenar el límite.

### Secretos y multi-entorno
- Config no-secreta → inline en el manifiesto plano (dev). Secretos → siempre `Secret` (dummy en dev, real por Sealed Secrets/ESO en prod), referenciados, nunca inline en `env:`. Así el Deployment no cambia entre dev y prod, solo la fuente del Secret.
- Estrategia multi-entorno self-host: **Kustomize** (base plana + overlays dev/prod) para la infra; **Helm** para los MS. El mix Helm+Kustomize es defendible (cada uno donde brilla) y retoma el plan original (CNPG + Kustomize).

### Conexión a BD (contratos distintos)
- Los MS usan una sola `DATABASE_URL` desde la clave `uri` del secret CNPG (contrato Python/SQLAlchemy: `postgresql://...`).
- Keycloak usa 3 env separadas desde el secret `keycloak-db-app`: `KC_DB_URL`←`jdbc-uri` (formato JDBC, `uri` no le sirve), `KC_DB_USERNAME`←`username`, `KC_DB_PASSWORD`←`password`. Keycloak no lo exige (el `jdbc-uri` embebe creds), pero 3 separadas mantienen el password fuera de la URL (menos fuga en logs).

### Tres planos de seguridad (aclaración conceptual)
- NetworkPolicy (L3/4, quién manda paquetes) ≠ RBAC de k8s (quién llama a la API de k8s) ≠ OIDC/Keycloak (auth de app). Los pods de app no necesitan tocar la API de k8s → KSA sin RoleBindings + `automountServiceAccountToken: false`. Cerrar el UI de Keycloak es NetworkPolicy + login admin propio, no RBAC de k8s.

### Scripts
- `k8s/install.sh` orquestador (mapa fase→script, sin lógica) + `scripts/NN-*.sh` single-responsibility + `scripts/lib.sh` con wrappers `kc`/`h` que pinnean `--context`/`--kube-context` (imposible instalar en el cluster equivocado). Instalaciones idempotentes (`helm upgrade --install`, guards de existencia). Logs en cada hito para no ser caja negra.

## Open questions
- **ORS bloqueado**: el seed `.osm.pbf` y el `graphs/` no están en el repo (solo `infra/ors/config/`, que sí está y es git-tracked). El `.pbf` hay que re-bajarlo (extract OSM de Bogotá). El grafo es artefacto build-once (cache): ORS lo construye del `.pbf` la 1ª vez y lo reusa; conviene persistir el grafo construido (PVC + backup en MinIO) y NO reconstruir por entorno. ORS es la dep pesada (~6GB de heap).
- Método de instalación de CNPG: se fue por Helm; queda abierta la opción del manifiesto versionado (`kubectl apply`).

## Next steps
- Rellenar `config.yml`/`secret.yml`/`realm.yml` de Keycloak (deferido; el Deployment ya los referencia).
- Fase 1: ejecutar y validar cluster kind + Cilium (aún no se ha corrido nada).
- Desplegar deps planas restantes (MinIO, MLflow) y luego Kafka (CR Kafka de Strimzi + KafkaTopic, reemplazando el topic-init).
- Fase 5 (exposición): Gateway API + cuadrar el issuer de Keycloak (`KC_HOSTNAME` == `KC_ISSUER` == URL del navegador); añadir `extraPortMappings` al kind config.
- Fase 6: NetworkPolicies (default-deny + allow cross-service; en `identity`, BD solo accesible desde pods de Keycloak).
- Makefile con targets `up`/`down`/`reset`/`smoke` sobre `install.sh`.
- Eje de entornos: sacar `env` a `values/dev.yaml` (MS) y overlays de Kustomize (infra).