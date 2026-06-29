---
title: Chrome subresource hang in devcontainer + properties-service 503 from StrictBase
captured-from: conversation
captured-on: 2026-06-28
participants: [raul, claude]
---

## Context
Debugging why `POST /v1/properties/create` was stale in Chrome but worked in Firefox, and why it returned 503 in Firefox before the Chrome issue was investigated.

## Key conclusions

### Bug 1 — properties-service 503 on create property
- `NeighborhoodInfo` and `LocationInfo` in `backend/properties-service/src/app/services/shared/schemas/catalog_schemas.py` extended `StrictBase` (`extra="forbid"`).
- Catalog-service returns extra fields (`search_name`, `latitude`, `longitude`) that Pydantic rejected → `ValidationError` → caught by `except Exception` in `CatalogAdapter.get_neighborhood()` → re-raised as `CatalogServiceUnavailableError` → 503.
- **Fix**: changed both schemas to use a new `_ExternalSchema(BaseModel)` base with `extra="ignore"`. External API response schemas must never use `extra="forbid"`.

### Bug 2 — Chrome subresource requests to localhost ports hang indefinitely
- `fetch()` / axios requests from a page at `localhost:8080` to `localhost:8003` (or any other localhost port) hang indefinitely in Chrome — no response, no CORS error, no rejection.
- Direct browser tab navigation to `localhost:8003` works fine. Firefox works fine.
- Root cause: VS Code devcontainer port forwarding adds a Node.js proxy layer. Chrome's HTTP keep-alive connection reuse interacts badly with this proxy after an auth retry cycle (401 → refresh → retry). The retry tries to reuse a connection the proxy already considers closed; Chrome stalls instead of opening a new one. Firefox handles the broken pipe more defensively.
- The same stall occurs for any fetch() to localhost:8003 once the pool is in a bad state (even a simple `GET /openapi.json` hangs).
- Flushing Chrome's socket pool (`chrome://net-internals/#sockets`) did not fix it reliably because the pool gets re-corrupted.
- **Fix**: configure Vue CLI `devServer.proxy` to route all API traffic through webpack dev server (same-origin from Chrome's perspective). API base URLs changed from absolute (`http://localhost:800x`) to relative (`/api/users`, `/api/catalog`, `/api/properties`, `/api/avm`). Webpack forwards internally to the container — no cross-origin machinery involved.
- Production: set `VUE_APP_*_URL` env vars to the real service URLs.

## Proxy config added (vue.config.js)
```js
devServer: {
  proxy: {
    "/api/users":      { target: "http://localhost:8000", changeOrigin: true, pathRewrite: { "^/api/users": "" } },
    "/api/catalog":    { target: "http://localhost:8001", changeOrigin: true, pathRewrite: { "^/api/catalog": "" } },
    "/api/avm":        { target: "http://localhost:8002", changeOrigin: true, pathRewrite: { "^/api/avm": "" } },
    "/api/properties": { target: "http://localhost:8003", changeOrigin: true, pathRewrite: { "^/api/properties": "" } },
  }
}
```

## Rule derived
External API response schemas (anything that calls `model_validate` on a third-party or inter-service HTTP response) must use `extra="ignore"`, not `extra="forbid"`. Only schemas that define the domain's own input contracts should use `StrictBase`.

## Open questions
- None. Both bugs resolved and confirmed working.

## Next steps
- Production deployment: add `VUE_APP_*_URL` env vars to CI/CD or `.env.production`.
