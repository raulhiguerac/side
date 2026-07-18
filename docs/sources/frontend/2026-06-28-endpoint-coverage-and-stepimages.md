---
title: Cobertura de endpoints frontend y diseño StepImagenes
captured-from: conversation
captured-on: 2026-06-28
participants: [raul, claude]
---

## Context

Auditoría completa de todos los endpoints de los 4 microservicios contra las llamadas reales del frontend, realizada leyendo los routers .py de cada servicio. También se diseñó y creó el componente `StepImagenes` como paso 3 del create property flow.

## Key conclusions

### Cobertura de endpoints (2026-06-28)

| Servicio | Cableados | Total |
|----------|-----------|-------|
| users-service | 13 | 20 |
| catalog-service | 6 | 20 |
| properties-service | 6 | 22 |
| analytics-service | 1 | 1 |
| **Total** | **26** | **63** |

**Endpoints faltantes críticos para MVP** (no admin, no edge flows):
- `POST /properties/images/presigned-urls` — bloquea el create flow
- `POST /properties/{id}/images/confirm` — parte del mismo flujo
- `PATCH /properties/{id}` — editar listing
- `POST /properties/{id}/visibility` — pausar/activar listing
- `POST /users/me/profile/photo` — foto de perfil

**Hallazgo crítico**: el front llama `POST /auth/login/google` que **no existe en el backend**.

**Endpoints marcados como internos/deprecated** (no requieren wiring en front):
- `GET /catalog/geo-resolution/resolve-neighborhood` — deprecated, reemplazado por `/by-coordinates`
- `GET /catalog/localities/by-id` — sin consumidor externo; solo se usa dentro del catalog para update UC
- `GET /catalog/localities/by-admin-division` — para futura UI de selector de departamento
- Todos los `/admin/*` de catalog y properties — van en panel admin, fase posterior

### Diseño de StepImagenes

- Componente en `frontend/src/components/properties/create/StepImagenes.vue`
- Paso 3 del create property form — las imágenes **no son opcionales**
- Expone `files` vía `defineModel<File[]>({ default: () => [] })` — el padre accede al array para las API calls
- El flujo de upload lo cablea el padre (no el componente):
  1. `POST /properties/images/presigned-urls` con `{ property_id, create_count }` → `{ batch_id, items[{ upload_url, public_url, key }] }`
  2. `PUT <upload_url>` por cada imagen (directo a MinIO)
  3. `POST /properties/{id}/images/confirm` con `{ batch_id, confirmed_keys: [...] }` — solo los keys de PUTs exitosos
- Al confirmar exitosamente → `router.push('/properties')`
- Botón "Publicar" deshabilitado si `selectedFiles.length === 0`
- `StepImagenes` se monta solo cuando `currentStep === 3 && !error` (la propiedad ya fue creada en el POST del paso 2)

### Ruta dev para visualización

- `GET /#/dev/imagenes` → `StepImagenesDevView.vue` — permite ver el componente sin pasar por el flujo completo del form

## Open questions

- ¿`/auth/login/google` se implementa en el backend o se quita del front?

## Next steps

- Cablear los 3 endpoints de imágenes en el create flow (`presigned-urls` → PUT → `confirm`)
- Cablear `PATCH /properties/{id}` para edición de listings
- Cablear `POST /properties/{id}/visibility` para pausar/activar
