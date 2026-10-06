---
title: "ADR-0010 — Moderar se hace en el panel de vista previa, con un formulario de guardado explícito"
status: stable
last-verified: 2026-08-02
owners: [frontend]
related:
  - "[[frontend-admin-panel]]"
  - "[[adr-tanstack-table]]"
  - "[[adr-no-component-library]]"
  - "[[adr-admin-tabs-nested-routes]]"
  - "[[properties-service-admin]]"
  - "[[adr-verification-reversible-lifecycle]]"
  - "[[open-items]]"
sources: [../../../sources/frontend/2026-08-02-moderation-panel-form-over-buttons.md]
decision-date: 2026-08-02
decision-status: accepted
---

# ADR-0010 — Moderar se hace en el panel de vista previa, con un formulario de guardado explícito

## Contexto

Con los endpoints de moderación listos, había que decidir dónde viven las acciones. El primer diseño —una columna de acciones en la tabla, después una barra de botones— se construyó y se descartó antes de cablearla a nada.

## Decisión

**1. Las acciones viven en el panel de vista previa, no en la tabla.**

El argumento que decide: **moderar exige mirar.** Aprobar desde una fila de la tabla es aprobar sin ver las fotos, que es exactamente lo que la verificación debería impedir — y las columnas disponibles (tipo, precio, fecha) no alcanzan para decidir nada. Actuar tiene que costar lo mismo que mirar.

La tabla queda como índice: nunca pasa el slot `#actions`, así que `AdminPropertiesTable` no agrega la columna de acciones y no hubo que tocarla. El click en fila sigue siendo solo selección.

**2. Un formulario con borrador y botón "Guardar", no botones de acción instantánea.**

`AdminModerationForm.vue`: dos selects precargados con el estado actual, los cambios se acumulan en local, y un "Guardar" aplica.

**3. Los selects ofrecen el estado actual más los destinos legales, y nada más.**

Llegar a `verified` desde `unverified` son dos guardados por construcción, porque `verified` simplemente no está en la lista. La regla de los dos saltos se comunica en vez de explotar como un 409. `constants/moderationTransitions.ts` espeja las dos tablas del backend.

**4. El motivo del rechazo es inline, no un modal.** Aparece bajo el select solo al elegir "Rechazada", con contador de 500 caracteres, y "Guardar" queda deshabilitado mientras esté vacío.

## Alternativas consideradas

- **Una columna por acción en la tabla.** Descartada: qué acciones son legales varía por fila, así que la mayoría de las celdas quedarían vacías —y una celda vacía no comunica "no aplica"—, y entre las dos máquinas una fila puede tener hasta 6 acciones legales contra 6 columnas de datos.
- **Barra de botones instantáneos en el panel** (construida como `AdminModerationActionBar.vue` y borrada). Tres problemas la mataron: un botón visible más un menú `⋯` escondido no se descubre; moderar los dos ejes eran dos requests y dos refetches; y con la tabla filtrada por `verification_status=pending`, cambiar la verificación **saca la fila de la lista antes** de poder hacer el segundo cambio. El caso de dos cambios no era lento, era imposible.
- **Botones en la fila *y* en el panel.** Descartada por redundante, y porque el atajo de la fila reintroduce el problema de moderar sin mirar.
- **Un botón "Aprobar" destacado encima del formulario** para la acción dominante. Diferida, no descartada: complica el estado del formulario antes de tener evidencia de que el click extra molesta.

## Consecuencias

- ✅ Es imposible moderar sin tener la property a la vista: el formulario va detrás de `v-if="property"`, así que ni siquiera se dibuja mientras la foto carga.
- ✅ Un solo refetch por sesión de edición, y la fila sale del filtro cuando el trabajo terminó, no en medio.
- ✅ La máquina de estados queda visible en la UI en vez de ser un misterio que se descubre por errores 409.
- ❌ **La acción dominante pasa de un click a dos.** En una cola filtrada por `pending` la mayoría de las filas solo necesitan "aprobar". Se asumió a cambio de que el caso de dos ejes deje de ser imposible.
- ❌ **Un "Guardar" pueden ser dos requests no atómicos.** Son endpoints distintos; si el segundo falla con 409 el primero ya se aplicó. El formulario tiene que reportar éxito/fallo por eje y recargar, no fingir atomicidad.

## Claims

- `AdminPropertiesModerationView` no pasa el slot `#actions` a `AdminPropertiesTable`, así que la columna de acciones no se agrega (frontend/src/views/admin/properties/AdminPropertiesModerationView.vue, frontend/src/components/admin/properties/AdminPropertiesTable.vue).
- `AdminModerationForm.vue` mantiene los cambios en `ref`s locales y solo emite en el click de "Guardar" (frontend/src/components/admin/properties/AdminModerationForm.vue).
- Las opciones de cada select se construyen desde `VERIFICATION_TRANSITIONS` y `LISTING_STATUS_TRANSITIONS`, que espejan las tablas del backend (frontend/src/constants/moderationTransitions.ts).
- El textarea del motivo se renderiza solo cuando el target elegido es `rejected` (frontend/src/components/admin/properties/AdminModerationForm.vue).
- `AdminModerationForm` no importa `propertiesApi` ni ningún endpoint; emite `save` con el payload (frontend/src/components/admin/properties/AdminModerationForm.vue).
- El formulario se monta detrás de `v-if="property"` dentro de `AdminPropertyPreviewPanel` (frontend/src/components/admin/properties/AdminPropertyPreviewPanel.vue).
