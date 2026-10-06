---
inclusion: always
---

# Producto

`side` es un marketplace inmobiliario (hoy solo Bogotá): publicar y buscar propiedades, un avalúo automático (AVM) y un panel admin para moderar listings y mantener el catálogo geográfico.

| Servicio | Responsabilidad |
|---|---|
| `users-service` | identidad y perfiles; único que gestiona usuarios en Keycloak |
| `catalog-service` | todo lo geográfico: países → divisiones → localidades → barrios, `(lat, lon) → barrio`, POIs e isócronas |
| `properties-service` | listings, imágenes, feed público, panel admin (moderación, promociones, bulk) |
| `analytics-service` | AVM (`/predict`) y predicciones async por Kafka |
| `frontend` | SPA Vue 3 que consume los cuatro |

La documentación vive en `docs/wiki/` (índice en `docs/INDEX.md`); los pendientes conocidos, en `docs/wiki/_shared/open-items.md`.
