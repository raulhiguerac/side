import { ref, watch, type Ref } from "vue";

// Arranca en la primera fila y se corrige si la elegida sale de la lista.
export function useRowSelection<T>(
  rows: Ref<T[]>,
  key: (row: T) => string = (row) => (row as { id: string }).id // promociones eligen por `property_id`
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
