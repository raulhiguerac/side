---
title: Cableado de moderación y armazón de promociones en el panel admin
captured-from: conversation
captured-on: 2026-08-09
participants: [author, claude]
---

## Context

El formulario de moderación existía pero su `save` no llegaba a ningún caller: no
había forma de moderar desde la UI. Cerrado eso, se diseñó la tab de Promociones,
que era el último hueco del panel admin.

## Key conclusions

- **El guardado de moderación se ejecuta desde la vista, no desde el panel.** Lo
  que hay que refrescar después incluye la lista, que es de la vista; el panel
  solo reenvía lo que cambió con el id que está mostrando.
- **`useModerateProperty` manda la verificación antes que el estado.** Si solo
  entra uno de los dos PATCH, conviene que sea el que decide si la property sigue
  en la cola: aprobada sin publicar es revisable, publicada sin resolver se
  escapó de la cola.
- **`moderate()` devuelve "algo quedó escrito", no "salió todo bien".** Un fallo
  parcial también deja viejo lo mostrado, así que obliga a refetchear igual; el
  mensaje distingue el caso para que el reintento no choque contra la mitad ya
  aplicada.
- **`reload()` refetchea la página actual y descarta las siguientes**
  (`usePagination.replaceCurrentPage`): al salir una fila del filtro todas se
  corren un lugar, y conservarlas mostraría duplicados al avanzar. `load()` queda
  para aplicar o cambiar filtros, porque resetea a la página 1.
- **El panel se recarga a mano solo si la fila sobrevivió al refetch**; si la
  selección se movió, su watcher de `propertyId` ya está cargando la nueva.
- **Promocionar no va en el panel de moderación.** Son dos trabajos distintos
  (control de políticas vs. vender ubicación), y el panel tendría que cargar
  estado comercial —si ya hay promoción activa— para pintar el botón.
- **Promociones se resuelve con sub-tabs, no con un modal**: `Activas`
  (`/promotions`) para revisar y quitar, `Promocionar` (`/promotions/new`) para
  crear, cada una con su tabla y el mismo panel de preview.
- **La tab Promocionar reusa el composable y la tabla de moderación**; lo único
  propio es el filtro `{ status: "active", is_promoted: false }`, que son las dos
  reglas que valida `CreatePromotionUseCase`.
- **Tabla + preview le gana a un grid de cards** para promociones: el grid no
  tiene dónde poner prioridad ni comparar vencimientos, que es lo único que la
  promoción decide.
- **Abstracciones extraídas al aparecer el segundo consumidor**: `AdminSplitView`
  (reparto 60/40, error, contenedor de tabla, aside sticky), `useRowSelection`
  (selección válida frente a cambios de la lista) y `AdminTabsNav`.
- **`AdminTabsNav` decide el matching por tab**: si su ruta es prefijo de otra
  matchea exacto, si no por prefijo. Así "Moderación" no se enciende de más y
  "Promociones" sigue activa dentro de sus sub-rutas.
- **Props que dependen de campos nuevos del backend llevan default.** Front y
  backend se despliegan por separado: `allowed_*` sin default reventaba el panel
  entero contra un backend viejo.
- **Los comentarios de bloque bajan a una línea**: el porqué en la línea, el
  detalle en la wiki.
- **Estructura por sub-dominio en `admin/`**: `shared/` para lo transversal,
  `properties/{moderation,promotions,imports}/` para lo específico, y lo usado
  por más de una tab queda en la raíz de `properties/`.

## Open questions

- El pie del panel de preview es el `AdminModerationForm` fijo: en las vistas de
  promociones va a aparecer apenas haya filas y su "Guardar" no va a ningún lado.
  Acordado que debe pasar a slot, sin implementar.
- `useRowSelection` devuelve la selección pero no acepta la fila; se propuso
  exponer un `select(row)` y quedó sin decidir.
- Las columnas que darían sentido a la tab Activas —prioridad y vencimiento— no
  existen en la respuesta: `GET /admin/promotions` devuelve `PropertyCardSchema`.
- El filtro por `verification_status` de la vista de moderación sigue pendiente;
  con él, la selección debería conservar el índice en vez de saltar a la primera
  fila.

## Next steps

- Cablear la tab Activas contra `GET /admin/promotions` y el POST/DELETE de
  promociones.
- Pasar el pie del panel a slot antes de cablear promociones.
- Cerrar el filtro de moderación y ajustar `useRowSelection` para no saltar al
  tope al desaparecer la fila moderada.
