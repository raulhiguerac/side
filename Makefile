# Entorno de desarrollo del monorepo side.
# Todo corre en contenedores: el unico requisito del host es Docker.

SHELL := /bin/bash
COMPOSE := docker compose
MC := docker run --rm --user $$(id -u):$$(id -g) -e HOME=/tmp -v "$$(PWD):/w" -w /w --entrypoint sh minio/mc

.DEFAULT_GOAL := help
.PHONY: help bootstrap up down stop reset seed data-pull logs ps

help: ## Muestra esta ayuda
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

# --- Guardas -----------------------------------------------------------------

check-env:
	@test -f .env.local || { \
		echo "ERROR: falta .env.local."; \
		echo "  cp .env.local.example .env.local  y completa los 7 valores"; \
		exit 1; }
	@grep -qE '^R2_BUCKET=.+' .env.local || { \
		echo "ERROR: .env.local no tiene las claves de R2 (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,"; \
		echo "       R2_SECRET_ACCESS_KEY, R2_BUCKET). Descomentalas y completalas."; \
		exit 1; }

check-artifacts:
	@test -f infra/ors/files/bogota.osm.pbf || { echo "ERROR: falta el .pbf. Corre 'make bootstrap'."; exit 1; }
	@test -f infra/seeds/catalog_geo.sql.gz || { echo "ERROR: faltan los seeds. Corre 'make bootstrap'."; exit 1; }
	@test -f infra/mlflow/registry/mlflow.db || { echo "ERROR: falta el registro de MLflow. Corre 'make bootstrap'."; exit 1; }

# --- Artefactos --------------------------------------------------------------

bootstrap: check-env ## Baja de R2 lo que no vive en git (~85 MB): pbf, seeds y modelo AVM
	@set -a; . ./.env.local; set +a; \
	$(MC) -c "mc alias set r2 https://$$R2_ACCOUNT_ID.r2.cloudflarestorage.com \
		$$R2_ACCESS_KEY_ID $$R2_SECRET_ACCESS_KEY --api S3v4 >/dev/null && \
		mc mirror --overwrite r2/$$R2_BUCKET/runtime/ /w/"
	@echo "bootstrap: ok"

data-pull: check-env ## Baja los datasets pesados de entrenamiento (~480 MB). Opcional.
	@set -a; . ./.env.local; set +a; \
	$(MC) -c "mc alias set r2 https://$$R2_ACCOUNT_ID.r2.cloudflarestorage.com \
		$$R2_ACCESS_KEY_ID $$R2_SECRET_ACCESS_KEY --api S3v4 >/dev/null && \
		mc mirror --overwrite r2/$$R2_BUCKET/datasets/ /w/"

# --- Ciclo de vida -----------------------------------------------------------

up: check-artifacts ## Levanta todo el stack
	$(COMPOSE) up -d
	@echo ""
	@echo "  users      http://localhost:8000/docs"
	@echo "  catalog    http://localhost:8001/docs"
	@echo "  properties http://localhost:8002/docs"
	@echo "  analytics  http://localhost:8003/docs"
	@echo "  frontend   http://localhost:8080"
	@echo "  keycloak   http://localhost:8180   admin/admin"
	@echo "  minio      http://localhost:9001   minioadmin/minioadmin"
	@echo "  mlflow     http://localhost:5000"
	@echo ""
	@echo "  login de dev: dev@example.com / dev12345 (rol admin)"

seed: ## Restaura los dumps y crea el usuario dev (idempotente)
	$(COMPOSE) up seed-db seed-dev-user

stop: ## Para los contenedores sin borrar nada
	$(COMPOSE) stop

down: ## Baja el stack conservando los volumenes
	$(COMPOSE) down

reset: ## DESTRUCTIVO: borra volumenes y grafos de ORS, y vuelve a levantar de cero
	@echo "Esto borra las 5 bases, MinIO, MLflow y los grafos de ORS."
	@echo "Lo que vive en R2 se recupera con 'make bootstrap'; lo demas no."
	@read -p "Escribi 'si' para continuar: " ok; [ "$$ok" = "si" ] || { echo "cancelado"; exit 1; }
	$(COMPOSE) down -v
	find infra/ors/graphs -mindepth 1 ! -name .gitkeep -exec rm -rf {} +
	$(MAKE) up

logs: ## Sigue los logs de todos los servicios
	$(COMPOSE) logs -f

ps: ## Estado de los servicios
	$(COMPOSE) ps
