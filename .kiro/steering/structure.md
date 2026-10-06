---
inclusion: always
---

# Estructura

```
backend/<servicio>-service/src/app/
  api/routes/        rutas FastAPI (las admin, en un paquete por entidad)
  api/deps/          inyección de dependencias: UoW, casos de uso, auth
  services/<dominio>/
    use_cases/       un caso de uso por archivo (en catalog_admin, una carpeta por entidad)
    ports/           typing.Protocol de los repositorios y la UoW
    adapters/        implementaciones SQL / HTTP
    schemas/         Pydantic (StrictBase: extra="forbid", from_attributes=True)
    helpers/
  core/              settings, excepciones de dominio, logging
  models/            tablas SQLModel
frontend/src/
  api/               una instancia de axios por servicio
  views/ components/ composables/ stores/
  types/admin/       un módulo por tema, sin index.ts
  constants/         endpoints y tamaños de página
docs/wiki/<servicio>/   páginas, ADRs y runbooks
docs/sources/<servicio>/ material inmutable que respalda la wiki
```

Los casos de uso dependen de ports, nunca de adapters. Las rutas solo arman el request y llaman a `execute`.
