---
title: "Gap de modelo: una Property no puede tener venta y arriendo simultáneos"
captured-from: conversation
captured-on: 2026-07-13
participants: [raul, claude]
---

## Context

Al decidir si `listing_type` debería ser editable en el flujo de edición de propiedades (ver `[[property-edit-fixed-vs-editable-fields]]`), surgió que el modelo de datos actual no soporta que un mismo inmueble físico tenga simultáneamente una oferta de venta y una de arriendo.

## Key conclusions

- `Property` es una tabla donde **una fila = una oferta con un `listing_type` fijo**. No existe relación entre filas que representen el mismo inmueble físico bajo distintas modalidades.
- Si un dueño quiere publicar el mismo inmueble en venta **y** en arriendo, hoy necesita crear **dos filas distintas** (dos `id` distintos, con `location`/`area_m2`/etc. duplicados manualmente) — sin ningún vínculo entre ellas.
- Consecuencia concreta: si el dueño vende la propiedad y solo actualiza (o elimina) la fila de venta, la fila de arriendo queda huérfana y sigue publicada, porque el sistema no sabe que están relacionadas.
- Por esto se descartó dejar `listing_type` editable: cambiarlo en la fila existente sería aún más confuso que el problema de arriba (el dueño podría pensar que está *agregando* una modalidad y en realidad está *transformando* la única oferta que tenía).

## Open questions

- Si se quiere soportar múltiples modalidades del mismo inmueble de forma prolija, hace falta diseñar la relación (ej. `parent_property_id` o una tabla de agrupación) — no evaluado en profundidad, solo identificado como deuda.

## Next steps

- No hay acción inmediata. Dejar este gap documentado para cuando el negocio pida soportar venta+arriendo del mismo inmueble.
