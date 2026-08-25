<template>
  <div
    class="border-brand-divider flex w-full flex-col gap-4 rounded-2xl border bg-white px-5 py-4 sm:flex-row sm:items-end"
  >
    <!-- Dos tercios para los filtros, uno para el disparador. -->
    <div class="flex min-w-0 flex-[2] flex-wrap gap-4">
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
        <select
          :id="`admin-filter-${filter.key}`"
          v-model="draft[filter.key]"
          :disabled="loading"
          class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
        >
          <!-- Sin la opción vacía, filtrar una vez esconde el resto para siempre. -->
          <option value="">{{ filter.allLabel ?? "Todas" }}</option>
          <option
            v-for="(label, value) in filter.options"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
      </div>
    </div>

    <div class="flex flex-1 justify-end">
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
import type { AdminFilterDefinition } from "@/types/admin";

/** Barra de filtros de las vistas admin: recibe los filtros con sus opciones y
 * devuelve los valores elegidos, sin saber qué se está filtrando. */
const props = withDefaults(
  defineProps<{
    filters: readonly AdminFilterDefinition[];
    /** Valores de arranque —hoy los de la URL—: sin esto un reload deja la lista
     * filtrada y los selects en blanco. */
    initial?: Record<string, string>;
    loading?: boolean;
  }>(),
  {
    initial: () => ({}),
    loading: false,
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

function apply() {
  // Las vacías se omiten: `verification_status=""` es un 422, el backend valida el enum.
  emit(
    "apply",
    Object.fromEntries(Object.entries(draft.value).filter(([, value]) => value))
  );
}

/** Manda el padre: tras aplicar cambia la URL y el borrador se resiembra desde ahí.
 * No hay bucle porque solo el click emite. */
watch(() => [props.filters, props.initial], syncFromInitial, {
  immediate: true,
});
</script>
