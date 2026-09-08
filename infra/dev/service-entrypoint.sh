#!/bin/sh
# Entrypoint de dev de los 4 microservicios: migra y arranca con hot-reload.
# Se monta desde infra/ para no duplicarlo en cuatro Dockerfiles.
set -eu

# alembic.ini vive en src/app y su env.py importa `models.*` (no `app.models`),
# asi que tiene que correr con ese directorio como cwd.
cd /app/src/app
echo "[$SERVICE_NAME] alembic upgrade head"
uv run --no-sync alembic upgrade head

cd /app
echo "[$SERVICE_NAME] uvicorn en :$SERVICE_PORT"
exec uv run --no-sync uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$SERVICE_PORT" \
  --reload \
  --reload-dir /app/src
