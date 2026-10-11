<template>
  <div class="grid grid-cols-2 gap-3">
    <div>
      <label
        class="text-brand-text mb-1 block text-sm font-medium"
        :for="`${idPrefix}-country`"
      >
        País
      </label>
      <select
        :id="`${idPrefix}-country`"
        v-model="countryId"
        :disabled="disabled"
        :class="SELECT_CLASSES"
        @change="$emit('countryChange')"
      >
        <option value="" disabled>Elige un país (obligatorio)</option>
        <option v-for="(label, id) in countryOptions" :key="id" :value="id">
          {{ label }}
        </option>
      </select>
    </div>
    <div>
      <label
        class="text-brand-text mb-1 block text-sm font-medium"
        :for="`${idPrefix}-locality`"
      >
        Localidad
      </label>
      <select
        :id="`${idPrefix}-locality`"
        v-model="localityId"
        :disabled="disabled || !countryId || loadingLocalities"
        :class="SELECT_CLASSES"
      >
        <option value="" disabled>
          {{
            loadingLocalities
              ? "Cargando…"
              : "Elige una localidad (obligatoria)"
          }}
        </option>
        <option v-for="(label, id) in localityOptions" :key="id" :value="id">
          {{ label }}
        </option>
      </select>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { AdminFilterOptions } from "@/types/admin/filters";

// Solo pinta: el estado y la carga viven en `useLocalityPicker`.
defineProps<{
  idPrefix: string;
  countryOptions: AdminFilterOptions;
  localityOptions: AdminFilterOptions;
  loadingLocalities: boolean;
  disabled?: boolean;
}>();

defineEmits<{ countryChange: [] }>();

const countryId = defineModel<string>("countryId", { required: true });
const localityId = defineModel<string>("localityId", { required: true });

const SELECT_CLASSES =
  "border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border bg-white px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50";
</script>
