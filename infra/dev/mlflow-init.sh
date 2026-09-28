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

# `rclone copy` salta lo que ya esta igual; `check` falla si falta o difiere algo.
rclone copy -q /artifacts/3/ s3:mlflow-artifacts/3/
rclone check -q --one-way /artifacts/3/ s3:mlflow-artifacts/3/
echo "  ok     artifacts -> s3://mlflow-artifacts/3/ ($(find /artifacts/3 -type f | wc -l) objetos)"
echo "mlflow-init: ok"
