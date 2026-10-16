<template>
  <div>
    <div class="grid gap-3" :style="{ gridTemplateColumns: columns }">
      <div v-for="field in fields" :key="field.key" class="min-w-0">
        <label
          class="text-brand-text mb-1 block text-sm font-medium"
          :for="`${idPrefix}-${field.key}`"
        >
          {{ field.label }}
        </label>
        <select
          :id="`${idPrefix}-${field.key}`"
          :value="model[field.key] ?? ''"
          :disabled="
            disabled ||
            cascade.isBlocked(field, model) ||
            cascade.loading.value[field.key]
          "
          class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border bg-white px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50"
          @change="onChange(field.key, $event)"
        >
          <option value="" disabled>
            {{
              cascade.loading.value[field.key]
                ? "Cargando…"
                : "Elige una opción"
            }}
          </option>
          <option
            v-for="(label, value) in cascade.options.value[field.key] ?? {}"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
      </div>
    </div>

    <p v-if="cascade.error.value" class="mt-2 text-sm text-red-600">
      {{ cascade.error.value }}
    </p>
  </div>
</template>

<script lang="ts" setup>
import { computed, toRaw, watch } from "vue";
import { useCascadeOptions } from "@/composables/admin/useCascadeOptions";
import type { AdminAsyncSelectFilter } from "@/types/admin/filters";

// Cascada obligatoria de los modales: mismas definiciones que la barra de filtros, sin "Todos".
const props = defineProps<{
  fields: readonly AdminAsyncSelectFilter[];
  idPrefix: string;
  disabled?: boolean;
}>();

const model = defineModel<Record<string, string>>({ required: true });

const cascade = useCascadeOptions(() => props.fields);

const columns = computed(
  () => `repeat(${props.fields.length}, minmax(0, 1fr))`
);

/** Lo último que emitimos: su vuelta por el v-model no debe recargar todo. */
let emitted: Record<string, string> | null = null;

function onChange(key: string, event: Event) {
  if (!(event.target instanceof HTMLSelectElement)) return;
  const next = { ...model.value, [key]: event.target.value };
  const dependents = cascade.dependentsOf(key);
  for (const field of dependents) next[field.key] = "";
  emitted = next;
  model.value = next;
  for (const field of dependents) cascade.load(field, next);
}

// Un objeto nuevo desde el padre (abrir el modal, precargar del filtro) recarga todas las opciones.
watch(
  model,
  (values) => {
    // toRaw: un `ref` del padre devuelve el objeto envuelto en un proxy.
    if (toRaw(values) !== emitted) cascade.loadAll(values);
  },
  { immediate: true }
);
</script>
