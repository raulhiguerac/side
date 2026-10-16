<template>
  <div class="space-y-3">
    <div class="grid grid-cols-2 gap-3">
      <div>
        <FormField label="Nombre" :input-id="`${idPrefix}-name`">
          <BaseInput
            :id="`${idPrefix}-name`"
            v-model="name"
            type="text"
            maxlength="150"
            placeholder="Obligatorio"
            :disabled="disabled"
          />
        </FormField>
      </div>
      <div>
        <FormField label="Nombre local" :input-id="`${idPrefix}-local-name`">
          <BaseInput
            :id="`${idPrefix}-local-name`"
            v-model="localName"
            type="text"
            maxlength="150"
            placeholder="Opcional"
            :disabled="disabled"
          />
        </FormField>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <FormField label="Tipo" :input-id="`${idPrefix}-type`">
          <BaseSelect
            :id="`${idPrefix}-type`"
            v-model="localityType"
            :disabled="disabled"
          >
            <option
              v-for="(label, value) in LOCALITY_TYPE_LABELS"
              :key="value"
              :value="value"
            >
              {{ label }}
            </option>
          </BaseSelect>
        </FormField>
      </div>
      <div>
        <FormField label="Zona horaria" :input-id="`${idPrefix}-timezone`">
          <BaseInput
            :id="`${idPrefix}-timezone`"
            v-model="timezone"
            type="text"
            maxlength="64"
            placeholder="America/Bogota"
            :disabled="disabled"
          />
        </FormField>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <FormField label="Latitud" :input-id="`${idPrefix}-latitude`">
          <BaseInput
            :id="`${idPrefix}-latitude`"
            v-model.number="latitude"
            type="number"
            step="any"
            min="-90"
            max="90"
            placeholder="Entre -90 y 90"
            :disabled="disabled"
            class="tabular-nums"
          />
        </FormField>
      </div>
      <div>
        <FormField label="Longitud" :input-id="`${idPrefix}-longitude`">
          <BaseInput
            :id="`${idPrefix}-longitude`"
            v-model.number="longitude"
            type="number"
            step="any"
            min="-180"
            max="180"
            placeholder="Entre -180 y 180"
            :disabled="disabled"
            class="tabular-nums"
          />
        </FormField>
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
        class="accent-brand-primary h-4 w-4 appearance-auto"
      />
      Capital de su división
    </label>
  </div>
</template>

<script lang="ts" setup>
import FormField from "@/components/shared/form/FormField.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
import BaseSelect from "@/components/shared/form/BaseSelect.vue";
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
</script>
