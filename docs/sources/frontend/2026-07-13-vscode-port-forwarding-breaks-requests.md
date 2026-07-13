---
title: "Dev gotcha: auto-port-forwarding de VS Code rompe requests a los microservicios locales"
captured-from: conversation
captured-on: 2026-07-13
participants: [raul, claude]
---

## Context

Al probar `MyPropertiesView.vue` en el navegador, `GET /v1/properties/me` devolvía 400 con body vacío, y el log de `properties-service` mostraba `WARNING uvicorn.error: Invalid HTTP request received.` — sin traceback, sin llegar a ningún handler de FastAPI.

## Key conclusions

- El síntoma (`Invalid HTTP request received.` + 400 sin body) es h11/uvicorn rechazando la conexión **a nivel de transporte**, antes de que la request llegue a cualquier ruta — no es un bug de lógica de negocio ni de auth.
- **Causa real**: `lsof -iTCP:8003` mostró que el puerto no lo tenía escuchando el proceso `fastapi dev --port 8003`, sino **VS Code** (proceso `code`) — el auto-port-forwarding del devcontainer había tomado el puerto y actuaba de proxy intermedio. Ese proxy no maneja perfecto todas las requests (particularmente con cookies/credentials), y eso rompía el parseo HTTP corriente abajo.
- **Diagnóstico**: si un endpoint devuelve 400 con body vacío y el log del backend muestra `Invalid HTTP request received.` sin ninguna otra línea de acceso normal para esa request, sospechar de un proxy intermedio (VS Code port-forwarding) antes que del código de la app.
- **Fix**: panel "Ports" de VS Code → quitar el forward del puerto en cuestión → reiniciar el proceso backend real si hace falta para que recupere el puerto.

## Open questions

- Ninguna.

## Next steps

- Si vuelve a pasar en otro puerto (8000/8001/8002), aplicar el mismo diagnóstico: `lsof -iTCP:<puerto>` para confirmar quién escucha antes de sospechar del código.
