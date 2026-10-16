import { ref } from "vue";
import type {
  AdminAsyncSelectFilter,
  AdminFilterDefinition,
  AdminFilterOptions,
} from "@/types/admin/filters";
import { logger } from "@/utils/logger";

const isAsync = (
  filter: AdminFilterDefinition
): filter is AdminAsyncSelectFilter => filter.type === "async-select";

/** Opciones de los `async-select` encadenados por `dependsOn`; los valores los pone quien llama. */
export function useCascadeOptions(
  filters: () => readonly AdminFilterDefinition[]
) {
  const options = ref<Record<string, AdminFilterOptions>>({});
  const loading = ref<Record<string, boolean>>({});
  const error = ref<string | null>(null);
  /** Por key: si el padre cambia dos veces rápido, la respuesta vieja no pisa a la nueva. */
  const latestRequest: Record<string, number> = {};

  function isBlocked(
    filter: AdminFilterDefinition,
    values: Record<string, string>
  ): boolean {
    return isAsync(filter) && !!filter.dependsOn && !values[filter.dependsOn];
  }

  async function load(
    filter: AdminAsyncSelectFilter,
    values: Record<string, string>
  ) {
    const request = (latestRequest[filter.key] ?? 0) + 1;
    latestRequest[filter.key] = request;

    let result: AdminFilterOptions = {};
    if (!isBlocked(filter, values)) {
      loading.value[filter.key] = true;
      try {
        result = await filter.loadOptions({ ...values });
      } catch (e) {
        error.value = `No se pudieron cargar las opciones de ${filter.label}`;
        logger.error("cascade options load failed", e);
      }
    }
    if (latestRequest[filter.key] !== request) return;
    options.value[filter.key] = result;
    loading.value[filter.key] = false;
  }

  function loadAll(values: Record<string, string>) {
    error.value = null;
    for (const filter of filters()) {
      if (isAsync(filter)) void load(filter, values);
    }
  }

  /** Hijos, nietos… de `key`, en orden: al cambiarlo hay que vaciarlos y recargarlos. */
  function dependentsOf(key: string): AdminAsyncSelectFilter[] {
    return filters()
      .filter(isAsync)
      .filter((filter) => filter.dependsOn === key)
      .flatMap((filter) => [filter, ...dependentsOf(filter.key)]);
  }

  return { options, loading, error, isBlocked, load, loadAll, dependentsOf };
}
