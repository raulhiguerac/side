---
inclusion: always
---

# Stack y comandos

- **Backend:** Python 3.10, FastAPI, SQLModel/SQLAlchemy (sesión síncrona), PostgreSQL + PostGIS, Redis, `uv`. Arquitectura hexagonal.
- **Frontend:** Vue 3 + TypeScript, Vue CLI 5 (webpack), Pinia, vue-router en hash mode, Tailwind, axios, Leaflet (`@vue-leaflet`), TanStack Table.
- **Infra de dev:** docker compose + devcontainer. Keycloak (`:8180`), SeaweedFS como S3, MLflow, Kafka, ORS. Puertos: users 8000, catalog 8001, properties 8002, analytics 8003, front 8080.

Los servicios corren dentro del devcontainer (`side-develop-1`). Cada servicio usa su propio venv: `UV_PROJECT_ENVIRONMENT=$HOME/.venvs/<servicio>`; no uses el venv compartido `/home/vscode/.venv` para varios servicios a la vez.

Verificación determinista (corre todo y deja `audit-report.txt` en la raíz):

```bash
make audit
```

Por servicio, dentro del devcontainer: `uv run --no-sync pytest -q tests/unit`, `uvx ruff check src tests`. Front: `node_modules/.bin/eslint src --ext .ts,.vue`, `node_modules/.bin/tsc --noEmit -p .`. El build del front (`npm run build`) conviene correrlo en el host: la VM de Docker tiene memoria limitada.
