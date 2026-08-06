#!/usr/bin/env bash
#
# 02-plataforma.sh — Fase 2: operador CloudNativePG + deps compartidas.
# Todo lo transversal vive en el namespace 'platform'.
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

log "Fase 2 — plataforma (CNPG + deps)"

# Namespaces: fuente única. Los 5 (users-ms, catalog-ms, properties-ms, analytics-ms,
# platform) con sus labels env=dev. Fase 3 hace 'helm -n <ns>' SIN --create-namespace.
log "creando namespaces"
kc apply -f "$K8S_DIR/bootstrap/namespaces.yml"

# --- Operadores -------------------------------------------------------------
# Solo CNPG y Strimzi (Kafka) van como operador; el resto de platform es plano.
# Viven en su namespace de SISTEMA, creado por el propio helm (--create-namespace):
# no son namespaces de app, así que no rompen la regla de "namespaces.yml es fuente única".
# --wait: deben estar Ready ANTES de la Fase 3 / de crear el Kafka (que usan sus CRs).
log "añadiendo repos de operadores (CNPG, Strimzi)"
h repo add cnpg https://cloudnative-pg.github.io/charts --force-update
h repo add strimzi https://strimzi.io/charts/ --force-update
h repo update

log "instalando operador CloudNativePG"
h upgrade --install cnpg cnpg/cloudnative-pg \
  --namespace cnpg-system --create-namespace --wait

# watchAnyNamespace=true → el operador gestiona Kafka en el namespace que elijamos luego.
log "instalando operador de Kafka (Strimzi)"
h upgrade --install strimzi strimzi/strimzi-kafka-operator \
  --namespace strimzi-system --create-namespace \
  --set watchAnyNamespace=true --wait

# TODO: desplegar Keycloak (+ su BD), Redis, MinIO, Kafka, MLflow, ORS
warn "deps de platform: pendiente"