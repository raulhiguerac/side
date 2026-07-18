---
title: Orden por created_at en listados de propiedades del dueño
captured-from: conversation
captured-on: 2026-07-13
participants: [raul, claude]
---

## Context

En `MyPropertiesView.vue` las propiedades no aparecían en un orden predecible. Se revisó `SqlPropertyRepository` y ninguna de las dos queries de listado por dueño tenía `ORDER BY` — el orden dependía de lo que Postgres devolviera, sin garantía de estabilidad.

## Key conclusions

- `get_user_properties` (usada por `GetMyPropertiesUseCase`, endpoint `GET /v1/properties/me`) no tenía `order_by`. Se agregó `.order_by(Property.created_at.desc())` — más nuevo primero.
- `get_public_user_properties` (usada por `GetPublicUserPropertiesUseCase`, endpoint `GET /v1/properties/users/{user_id}`, paginada con `LIMIT`/`OFFSET`) tampoco tenía `order_by`. Se agregó el mismo `.order_by(Property.created_at.desc())`, colocado **antes** de `.limit()`/`.offset()` — necesario para que la paginación por offset sea estable (sin orden determinístico, cambiar de página puede saltear o repetir filas).
- Ambos cambios en `backend/properties-service/src/app/services/listing/adapters/sql_property_repository.py`.

## Open questions

- Ninguna.

## Next steps

- Ninguno — cambio ya aplicado y no requiere wiring adicional en frontend (el orden lo resuelve la query, no el cliente).
