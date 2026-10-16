---
title: Tabs de divisiones y países del panel admin de catálogo
captured-from: conversation
captured-on: 2026-10-16
participants: [raul, claude]
---

## Context
Tras sacar las piezas compartidas del admin de catálogo (ver `2026-10-16-admin-localities-tab-and-shared-pieces.md`), Divisiones y Países se armaron como plantilla de Localidades. Lint y vue-tsc pasan; nada se probó en el navegador.

## Key conclusions
- **Con esto el front consume los 17 endpoints admin de catalog:** 8 de barrios y listar, crear y editar de localidades, divisiones y países. Ninguna tab de catálogo queda en `EmptyState`.
- **Divisiones:** filtros País y Estado (`DIVISION_FILTERS`); tabla con nombre, código, tipo, ISO y estado; panel con tipo e ISO 3166-2. Editar cambia nombre, tipo e ISO (`UpdateAdminDivisionRequest` no acepta código ni país). Crear lleva cascada solo de País, precargada del filtro. La acción **Localidades** hace `router.push` a `admin-catalog-localities` con `country_id` y `admin_division_id`.
- **Países:** filtros Estado y Soporte (`COUNTRY_FILTERS`, con `is_supported`); tabla con nombre, ISO alfa-2, moneda, soporte y estado; panel con nombre oficial y nativo, prefijo, moneda, idioma, zona horaria y soporte. Editar cambia todo salvo los códigos ISO. Crear pide alfa-2, alfa-3 y numérico, validados en el cliente (2 letras, 3 letras, 3 dígitos) y enviados en mayúsculas. La acción **Divisiones** hace `router.push` a `admin-catalog-admin-divisions` con `country_id`.
- Validación en el cliente para países: moneda de 3 letras (se manda en mayúsculas) y zona horaria IANA; el back no la hace.
- Los dos usan `useAdminPage`, `AdminFormModal`, `AdminStatusModal` y `AdminStatusBadge`; sus campos editables viven en `DivisionFormFields` y `CountryFormFields`, compartidos por crear y editar.
- `utils/localityForm.ts` pasó a `utils/catalogForms.ts` y valida las tres entidades (`isLocalityFormValid`, `isDivisionFormValid`, `isCountryFormValid`, `isIsoCodeValid`), más `toCountryFields`, que arma el body común de crear y editar país.
- `getAdminDivisions` quedó tipado con `PageParams & DivisionAdminFilters` en vez de los tipos `ListAdminDivisionsData` generados.
- Los modales de estado aclaran que no hay cascada: desactivar una división no cambia sus localidades, ni desactivar un país sus divisiones o localidades.
- **Limitación del select de País:** usa el `GET` público (solo activos). Al saltar desde un país inactivo, la tabla de divisiones sí se filtra pero el select se ve vacío.
- **Back (lo escribe el autor):** desactivar un país no lo saca de la lista pública hasta que expire el TTL, porque `UpdateCountryUseCase` no borra `cache_key_countries()` (ítem ya registrado). Crear y editar división escriben `cache_key_admin_division`, que nadie lee, y renombrar una división deja viejas las listas públicas de localidades (ítem nuevo en open-items).

## Open questions
- ¿El select de País de filtros y cascadas pasa al `GET` admin para poder elegir países inactivos?
- ¿Los paneles muestran el nombre de la división (localidades) y del país (divisiones), hoy solo con el id?

## Next steps
- Probar en navegador las cuatro tabs, los modales y los saltos País → Divisiones → Localidades → Barrios.
- Back: invalidar la lista pública de países en `UpdateCountryUseCase`; arreglar la cache de división y de localidad.
- Commit y PR del admin de catálogo.
- Pendiente aparte: unificar los `messageForError` y las clases de inputs repetidas.
