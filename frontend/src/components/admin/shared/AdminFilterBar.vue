<template>
  <div
    class="filter-grid border-brand-divider grid w-full gap-4 rounded-2xl border bg-white px-5 py-4"
    :style="gridVars"
  >
    <div v-for="filter in filters" :key="filter.key" class="min-w-0">
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

    <PrimaryButton
      type="button"
      :loading="loading"
      class="w-full self-end border border-transparent"
      @click="apply"
    >
      {{ loading ? "Buscando…" : "Aplicar" }}
    </PrimaryButton>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import type {
  AdminAsyncSelectFilter,
  AdminFilterDefinition,
  AdminFilterOptions,
} from "@/types/admin/filters";
import PrimaryButton from "@/components/shared/PrimaryButton.vue";

// Filtros genéricos: devuelve los valores elegidos sin saber qué filtran.
const props = withDefaults(
  defineProps<{
    filters: readonly AdminFilterDefinition[];
    /** Valores de arranque (la URL): sin esto un reload deja los selects en blanco. */
    initial?: Record<string, string>;
    loading?: boolean;
  }>(),
  {
    initial: () => ({}),
    loading: false,
  }
);

const emit = defineEmits<{ apply: [values: Record<string, string>] }>();

// El botón cuenta como celda: hasta 4 en una fila; desde 5 en dos (5 filtros → 3 + 3).
const gridVars = computed(() => {
  const n = props.filters.length + 1;
  return { "--cols": n <= 4 ? n : Math.ceil(n / 2) };
});

/** El borrador no sale hasta el click: elegir el segundo select no refetchea con el primero a medias. */
const draft = ref<Record<string, string>>({});

function syncFromInitial() {
  // Todas las keys, también vacías: si no, `<option value="">` no queda marcado.
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

// En @change y no en watch: sembrar desde la URL no debe vaciar los hijos.
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

// Manda el padre: al aplicar cambia la URL y el borrador se resiembra.
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

<style scoped>
@media (min-width: 640px) {
  .filter-grid {
    grid-template-columns: repeat(var(--cols), minmax(0, 1fr));
  }
}
</style>
