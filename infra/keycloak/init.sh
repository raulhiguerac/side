#!/bin/sh
# Reconcilia lo que el export del realm no puede traer.
# Idempotente: se re-aplica en cada `compose up` y funciona sobre un realm ya
# existente, que es justo lo que `--import-realm` no hace (salta si el realm ya
# esta: "Realm 'core' already exists. Import skipped").
set -eu

KCADM=/opt/keycloak/bin/kcadm.sh

$KCADM config credentials \
  --server "$KC_URL" \
  --realm master \
  --user "$KC_BOOTSTRAP_ADMIN" \
  --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" >/dev/null

client_id_of () {
  $KCADM get clients -r "$KC_REALM" -q "clientId=$1" --fields id --format csv --noquotes \
    | tr -d '\r' | head -1
}

# El partial-export enmascara los secrets como "**********", asi que los
# clientes confidenciales quedan sin secret utilizable hasta que se fijan aca.
set_client_secret () {
  id=$(client_id_of "$1")
  if [ -z "$id" ]; then
    echo "ERROR: el cliente '$1' no existe en el realm '$KC_REALM'" >&2
    exit 1
  fi
  $KCADM update "clients/$id" -r "$KC_REALM" -s "secret=$2"
  echo "  secret fijado: $1"
}

echo "keycloak-init: realm=$KC_REALM"
set_client_secret users-ms-admin "$KC_ADMIN_SECRET"
set_client_secret users-ms-auth "$KC_AUTH_SECRET"
echo "keycloak-init: ok"
