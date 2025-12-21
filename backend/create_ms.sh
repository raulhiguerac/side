#!/bin/bash
set -e

ms_name="$1"

if [ -z "$ms_name" ]; then
  echo "Usage: ./create-ms.sh <ms-name>"
  exit 1
fi

base="./$ms_name"

mkdir -p "$base/src/app"/{api,core,models,schemas,services,repositories,db,migrations,utils}
mkdir -p "$base/src/app/api"/{routers,deps}
mkdir -p "$base/tests"/{unit,integration}

touch "$base/src/app/__init__.py"
touch "$base/src/app/api/__init__.py"
touch "$base/src/app/api/routers/__init__.py"
touch "$base/src/app/core/__init__.py"
touch "$base/src/app/db/__init__.py"
touch "$base/src/app/schemas/__init__.py"

touch "$base/src/app/main.py"
touch "$base/src/app/api/routers/health.py"
touch "$base/src/app/core/config.py"
touch "$base/src/app/core/security.py"
touch "$base/tests/conftest.py"

touch "$base/Dockerfile"
touch "$base/.dockerignore"
touch "$base/.env.example"

cd "$base" && uv init && rm -f hello.py

echo "FastAPI microservice scaffold created at $base"