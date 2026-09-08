#!/bin/sh
# Restaura el registro y los artifacts del AVM antes de que arranque el server.
#
# Por que se restaura el sqlite y no se registra por API: el MLmodel del modelo
# trae horneados `artifact_path` (s3://mlflow-artifacts/3/models/m-62a127.../),
# `model_id` y `run_id`. Registrar por API generaria ids nuevos que no coinciden
# con los del propio artefacto. Por eso los artifacts van a esa ruta exacta.
#
# Corre ANTES que el server porque el backend store es sqlite: escribirle el
# archivo por debajo a un proceso vivo es pedir corrupcion.
set -eu

echo "mlflow-init:"

# El db solo se siembra si no hay ninguno. Nunca se pisa: un db existente puede
# tener experimentos posteriores al seed.
if [ -f /mlflow/mlflow.db ]; then
  echo "  skip   mlflow.db — ya existe en el volumen"
else
  if [ ! -f /registry/mlflow.db ]; then
    echo "  ERROR: falta infra/mlflow/registry/mlflow.db. Corriste 'make bootstrap'?" >&2
    exit 1
  fi
  cp /registry/mlflow.db /mlflow/mlflow.db
  echo "  carga  mlflow.db -> volumen mlflow_data"
fi

if [ ! -d /artifacts/3 ]; then
  echo "  ERROR: falta infra/mlflow/artifacts/3. Corriste 'make bootstrap'?" >&2
  exit 1
fi

mc alias set local "$MINIO_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null

# Centinela, igual que seed-db: `mc mirror` NO salta los objetos existentes,
# falla con "Overwrite not allowed" y ademas devuelve 0, asi que sin este
# chequeo el init reportaria exito sin haber sincronizado nada.
remote=$(mc ls --recursive local/mlflow-artifacts/3/ 2>/dev/null | wc -l)
local_n=$(mc ls --recursive /artifacts/3/ 2>/dev/null | wc -l)

if [ "$remote" -gt 0 ]; then
  echo "  skip   artifacts — s3://mlflow-artifacts/3/ ya tiene $remote objetos"
else
  mc mirror --quiet --exclude ".gitkeep" /artifacts/ local/mlflow-artifacts/
  remote=$(mc ls --recursive local/mlflow-artifacts/3/ 2>/dev/null | wc -l)
  if [ "$remote" != "$local_n" ]; then
    echo "  ERROR: se subieron $remote de $local_n objetos" >&2
    exit 1
  fi
  echo "  carga  artifacts -> s3://mlflow-artifacts/ ($remote objetos)"
fi
echo "mlflow-init: ok"
