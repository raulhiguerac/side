<template>
  <div
    class="border-brand-divider flex w-full flex-col gap-4 rounded-2xl border bg-white px-5 py-4 sm:flex-row sm:items-end"
  >
    <div
      class="flex min-w-0 flex-wrap gap-4"
      :class="filtersWidth === 'full' ? 'flex-1' : 'flex-[2]'"
    >
      <div
        v-for="filter in filters"
        :key="filter.key"
        class="min-w-0 flex-1 basis-48"
      >
        <label
          :for="`admin-filter-${filter.key}`"
          class="text-brand-muted mb-1 block text-xs font-semibold tracking-wide uppercase"
        >
          {{ filter.label }}
        </label>
        <input
          v-if="filter.type === 'search'"
          :id="`admin-filter-${filter.key}`"
          v-model="draft[filter.key]"
          type="search"
          :placeholder="filter.placeholder"
          :disabled="loading"
          class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
          @keydown.enter.prevent="apply"
        />
        <select
          v-else
          :id="`admin-filter-${filter.key}`"
          v-model="draft[filter.key]"
          :disabled="loading || isBlocked(filter)"
          class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
          @change="resetDependents(filter.key)"
        >
          <!-- Sin la opción vacía, filtrar una vez esconde el resto para siempre. -->
          <option value="">{{ filter.allLabel ?? "Todas" }}</option>
          <option
            v-for="(label, value) in optionsFor(filter)"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
      </div>
    </div>

    <div
      class="flex justify-end"
      :class="filtersWidth === 'full' ? 'flex-none' : 'flex-1'"
    >
      <button
        type="button"
        :disabled="loading"
        class="bg-brand-primary flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-bold text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-green-600 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto"
        @click="apply"
      >
        <BaseSpinner v-if="loading" class="h-4 w-4 text-white" />
        {{ loading ? "Buscando…" : "Aplicar" }}
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from "vue";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import type {
  AdminAsyncSelectFilter,
  AdminFilterDefinition,
  AdminFilterOptions,
} from "@/types/admin/filters";

/** Barra de filtros de las vistas admin: recibe los filtros con sus opciones y
 * devuelve los valores elegidos, sin saber qué se está filtrando. */
const props = withDefaults(
  defineProps<{
    filters: readonly AdminFilterDefinition[];
    /** Valores de arranque —hoy los de la URL—: sin esto un reload deja la lista
     * filtrada y los selects en blanco. */
    initial?: Record<string, string>;
    loading?: boolean;
    /** `two-thirds`: filtros 2/3 y botón 1/3. `full`: el botón ocupa solo su ancho. */
    filtersWidth?: "two-thirds" | "full";
  }>(),
  {
    initial: () => ({}),
    loading: false,
    filtersWidth: "two-thirds",
  }
);

const emit = defineEmits<{ apply: [values: Record<string, string>] }>();

/** El borrador no sale hasta el click: elegir el segundo select no refetchea con el primero a medias. */
const draft = ref<Record<string, string>>({});

function syncFromInitial() {
  // Se siembran todas las keys, incluso las vacías: sobre una key ausente el
  // `<option value="">` no tiene nada que marcar como seleccionado.
  draft.value = Object.fromEntries(
    props.filters.map((filter) => [filter.key, props.initial[filter.key] ?? ""])
  );
}

const asyncOptions = ref<Record<string, AdminFilterOptions>>({});
/** Por key: si el padre cambia dos veces rápido, la respuesta vieja no pisa a la nueva. */
const latestRequest: Record<string, number> = {};

function optionsFor(filter: AdminFilterDefinition): AdminFilterOptions {
  if (filter.type === "async-select")
    return asyncOptions.value[filter.key] ?? {};
  if (filter.type === "search") return {};
  return filter.options;
}

function isBlocked(filter: AdminFilterDefinition): boolean {
  return (
    filter.type === "async-select" &&
    !!filter.dependsOn &&
    !draft.value[filter.dependsOn]
  );
}

async function loadOptions(filter: AdminAsyncSelectFilter) {
  const request = (latestRequest[filter.key] ?? 0) + 1;
  latestRequest[filter.key] = request;

  let options: AdminFilterOptions = {};
  if (!isBlocked(filter)) {
    try {
      options = await filter.loadOptions({ ...draft.value });
    } catch {
      options = {};
    }
  }
  if (latestRequest[filter.key] === request)
    asyncOptions.value[filter.key] = options;
}

/** Al cambiar un padre se vacían sus hijos (y los hijos de esos) y se recargan.
 * Va en el `@change` y no en un watch: sembrar desde la URL no debe vaciar nada. */
function resetDependents(key: string) {
  for (const filter of props.filters) {
    if (filter.type !== "async-select" || filter.dependsOn !== key) continue;
    draft.value[filter.key] = "";
    loadOptions(filter);
    resetDependents(filter.key);
  }
}

function apply() {
  // Las vacías se omiten: `verification_status=""` es un 422, el backend valida el enum.
  emit(
    "apply",
    Object.fromEntries(Object.entries(draft.value).filter(([, value]) => value))
  );
}

/** Manda el padre: tras aplicar cambia la URL y el borrador se resiembra desde ahí.
 * No hay bucle porque solo el click emite. */
watch(
  () => [props.filters, props.initial],
  () => {
    syncFromInitial();
    for (const filter of props.filters) {
      if (filter.type === "async-select") loadOptions(filter);
    }
  },
  { immediate: true }
);
</script>
