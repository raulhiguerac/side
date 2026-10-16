<template>
  <div class="space-y-3">
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-name`">Nombre</label>
        <input
          :id="`${idPrefix}-name`"
          v-model="name"
          type="text"
          maxlength="150"
          placeholder="Obligatorio"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-local-name`">
          Nombre local
        </label>
        <input
          :id="`${idPrefix}-local-name`"
          v-model="localName"
          type="text"
          maxlength="150"
          placeholder="Opcional"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-type`">Tipo</label>
        <select
          :id="`${idPrefix}-type`"
          v-model="localityType"
          :disabled="disabled"
          :class="[INPUT_CLASSES, 'bg-white']"
        >
          <option
            v-for="(label, value) in LOCALITY_TYPE_LABELS"
            :key="value"
            :value="value"
          >
            {{ label }}
          </option>
        </select>
      </div>
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-timezone`">
          Zona horaria
        </label>
        <input
          :id="`${idPrefix}-timezone`"
          v-model="timezone"
          type="text"
          maxlength="64"
          placeholder="America/Bogota"
          :disabled="disabled"
          :class="INPUT_CLASSES"
        />
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-latitude`">
          Latitud
        </label>
        <input
          :id="`${idPrefix}-latitude`"
          v-model.number="latitude"
          type="number"
          step="any"
          min="-90"
          max="90"
          placeholder="Entre -90 y 90"
          :disabled="disabled"
          :class="[INPUT_CLASSES, 'tabular-nums']"
        />
      </div>
      <div>
        <label :class="LABEL_CLASSES" :for="`${idPrefix}-longitude`">
          Longitud
        </label>
        <input
          :id="`${idPrefix}-longitude`"
          v-model.number="longitude"
          type="number"
          step="any"
          min="-180"
          max="180"
          placeholder="Entre -180 y 180"
          :disabled="disabled"
          :class="[INPUT_CLASSES, 'tabular-nums']"
        />
      </div>
    </div>

    <label
      class="text-brand-text flex items-center gap-2 text-sm font-medium"
      :for="`${idPrefix}-capital`"
    >
      <input
        :id="`${idPrefix}-capital`"
        v-model="isCapital"
        type="checkbox"
        :disabled="disabled"
        class="accent-brand-primary h-4 w-4"
      />
      Capital de su división
    </label>
  </div>
</template>

<script lang="ts" setup>
import { LOCALITY_TYPE_LABELS } from "@/constants/localityLabels";
import type { LocalityType } from "@/types/admin/catalog";

// Campos editables, compartidos por crear y editar; código y cascada van en cada modal.
defineProps<{ idPrefix: string; disabled?: boolean }>();

const name = defineModel<string>("name", { required: true });
const localName = defineModel<string>("localName", { required: true });
const localityType = defineModel<LocalityType>("localityType", {
  required: true,
});
const timezone = defineModel<string>("timezone", { required: true });
// `v-model.number` deja "" si el campo queda vacío.
const latitude = defineModel<number | "">("latitude", { required: true });
const longitude = defineModel<number | "">("longitude", { required: true });
const isCapital = defineModel<boolean>("isCapital", { required: true });

const LABEL_CLASSES = "text-brand-text mb-1 block text-sm font-medium";
const INPUT_CLASSES =
  "border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none disabled:opacity-50";
</script>
