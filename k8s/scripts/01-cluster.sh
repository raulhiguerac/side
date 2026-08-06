#!/usr/bin/env bash
#
# 01-cluster.sh — Fase 1: cluster kind (SIN CNI) + Cilium.
# kind arranca con disableDefaultCNI → nodos NotReady hasta instalar Cilium.
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

log "Fase 1 — cluster kind '$CLUSTER_NAME'"

log "verificando prerequisitos: docker, kind, helm"
# 'docker info' falla si el CLI no está O si el daemon no corre (justo lo que queremos).
if ! docker info >/dev/null 2>&1; then
  warn "Docker no responde: verifica que esté instalado y el daemon corriendo."
  exit 1
fi

# kind: solo lo instalamos si no está ya (idempotencia).
if ! command -v kind >/dev/null 2>&1; then
  log "kind no encontrado, instalando v0.29.0"
  curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.29.0/kind-linux-amd64
  chmod +x ./kind
  sudo mv ./kind /usr/local/bin/kind
  kind version || { warn "Falla en la instalación de kind"; exit 1; }
fi

# helm: solo si no está ya. Lo necesitaremos para Cilium y los microservicios.
if ! command -v helm >/dev/null 2>&1; then
  log "helm no encontrado, instalando"
  curl -fsSL -o /tmp/get-helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
  chmod +x /tmp/get-helm.sh
  /tmp/get-helm.sh
  helm version || { warn "Falla en la instalación de helm"; exit 1; }
fi

# Crear solo si no existe (kind create falla si ya está, y set -e abortaría).
if kind get clusters | grep -qx "$CLUSTER_NAME"; then
  warn "cluster '$CLUSTER_NAME' ya existe, lo reuso"
else
  log "creando cluster kind (la 1ª vez descarga la imagen de nodo, puede tardar)…"
  kind create cluster --name "$CLUSTER_NAME" --config "$KIND_CONFIG"
  log "cluster creado — nodos en NotReady hasta instalar Cilium (esperado)"
fi

# --- Cilium (CNI) -----------------------------------------------------------
# Con kubeProxyReplacement=true Cilium necesita saber DÓNDE está la API server
# (sin kube-proxy no hay ClusterIP que resuelva el service 'kubernetes'). En kind
# eso es la IP del contenedor control-plane en la red docker 'kind', puerto 6443.
# (Talos usaba localhost:7445 = su KubePrism; aquí NO aplica.)
log "añadiendo repo de Helm de Cilium"
h repo add cilium https://helm.cilium.io/ --force-update
h repo update

API_IP="$(docker inspect -f '{{(index .NetworkSettings.Networks "kind").IPAddress}}' "${CLUSTER_NAME}-control-plane")"
log "API server del cluster detectada en ${API_IP}:6443"

# upgrade --install → idempotente (no peta si el release ya existe).
# gatewayAPI.enabled lo dejamos para la Fase 5 (necesita sus CRDs antes).
log "instalando Cilium (CNI + kubeProxyReplacement)…"
h upgrade --install cilium cilium/cilium \
  --namespace kube-system \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost="$API_IP" \
  --set k8sServicePort=6443

# Cilium tarda en programar la red: esperamos al DaemonSet y a que los nodos pasen a Ready.
log "esperando a que Cilium arranque en todos los nodos…"
kc -n kube-system rollout status ds/cilium --timeout=180s
log "esperando a que los nodos pasen a Ready…"
kc wait --for=condition=Ready nodes --all --timeout=120s
log "Fase 1 completa — cluster '$CLUSTER_NAME' Ready con Cilium ✓"