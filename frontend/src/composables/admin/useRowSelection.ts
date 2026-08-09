import { ref, watch, type Ref } from "vue";

/**
 * La fila elegida del listado, que es lo que mira el panel de la derecha.
 *
 * Arranca con la primera ya elegida en vez de vacío, y se vigila la lista
 * entera —no solo la carga inicial— porque al paginar o refetchear cambia el
 * conjunto: la seleccionada puede dejar de estar visible y quedaría marcada una
 * fila que no se ve. Si sigue en la lista, no se toca.
 *
 * `key` existe porque no siempre se selecciona por el `id` de la fila: el
 * listado de promociones lista promociones, pero lo que el panel necesita es el
 * `property_id`.
 */
export function useRowSelection<T>(
  rows: Ref<T[]>,
  key: (row: T) => string = (row) => (row as { id: string }).id
) {
  const selectedId = ref<string | null>(null);

  watch(
    rows,
    (list) => {
      if (!list.length) {
        selectedId.value = null;
        return;
      }
      if (!list.some((row) => key(row) === selectedId.value)) {
        selectedId.value = key(list[0]);
      }
    },
    { immediate: true }
  );

  return { selectedId };
}
