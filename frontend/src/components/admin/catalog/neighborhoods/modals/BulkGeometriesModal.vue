<template>
  <BaseModal :model-value="open" @update:model-value="onDismiss">
    <div class="mb-4 flex items-center gap-4">
      <div
        class="bg-brand-primary-light flex h-12 w-12 items-center justify-center rounded-xl"
      >
        <MapPinned class="text-brand-primary h-6 w-6" />
      </div>
      <h3 class="text-brand-text text-lg font-bold">Subir geometrías</h3>
    </div>

    <template v-if="result">
      <BulkResultSummary
        class="mb-6"
        :stats="[
          { label: 'Geometrías actualizadas', value: result.updated },
          { label: 'Barrios sin geometría', value: result.unmatched.length },
        ]"
        issues-title="Barrios de la localidad sin Feature"
        :issues="result.unmatched"
      />
      <button
        type="button"
        class="bg-brand-primary w-full rounded-xl py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90"
        @click="$emit('confirm')"
      >
        Listo
      </button>
    </template>

    <template v-else>
      <div class="mb-6 space-y-4">
        <LocalitySelectFields
          v-model:country-id="countryId"
          v-model:locality-id="localityId"
          id-prefix="bulk-geometries"
          :country-options="countryOptions"
          :locality-options="localityOptions"
          :loading-localities="loadingLocalities"
          :disabled="saving"
          @country-change="onCountryChange"
        />

        <div>
          <label
            class="text-brand-text mb-1 block text-sm font-medium"
            for="bulk-geometries-name-field"
          >
            Propiedad con el nombre del barrio
          </label>
          <input
            id="bulk-geometries-name-field"
            v-model="nameField"
            type="text"
            placeholder="Obligatoria, p. ej. name"
            :disabled="saving"
            class="border-brand-border text-brand-text focus:border-brand-primary w-full rounded-xl border px-3 py-2 text-sm transition-colors focus:outline-none"
          />
        </div>

        <FileUploadField
          v-model="file"
          :extensions="BULK_GEOMETRIES_UPLOAD.extensions"
          :max-size-mb="BULK_GEOMETRIES_UPLOAD.maxSizeMb"
          :requirements="BULK_GEOMETRIES_UPLOAD.requirements"
          :disabled="saving"
          @update:model-value="reset"
        />
      </div>

      <FormMessage v-if="error || optionsError" variant="error" class="mb-4">
        {{ error ?? optionsError }}
      </FormMessage>

      <div class="flex gap-3">
        <button
          type="button"
          :disabled="saving"
          class="text-brand-text flex-1 rounded-xl py-3 text-sm font-semibold transition-colors hover:bg-brand-bg disabled:opacity-50"
          @click="$emit('close')"
        >
          Cancelar
        </button>
        <button
          type="button"
          :disabled="!submittable"
          class="bg-brand-primary flex-1 rounded-xl py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          @click="onSave"
        >
          {{ saving ? "Subiendo…" : "Subir" }}
        </button>
      </div>
    </template>
  </BaseModal>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { MapPinned } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import FileUploadField from "@/components/admin/shared/FileUploadField.vue";
import BulkResultSummary from "@/components/admin/catalog/neighborhoods/widgets/BulkResultSummary.vue";
import LocalitySelectFields from "@/components/admin/catalog/neighborhoods/widgets/LocalitySelectFields.vue";
import { useBulkEnrichGeometries } from "@/composables/admin/useBulkEnrichGeometries";
import { useLocalityPicker } from "@/composables/admin/useLocalityPicker";
import { BULK_GEOMETRIES_UPLOAD } from "@/constants/catalogUploads";
import type { BulkGeometriesResult } from "@/types/admin/catalog";

const props = defineProps<{
  open: boolean;
  initialCountryId: string | null;
  initialLocalityId: string | null;
}>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const { saving, error, upload, reset } = useBulkEnrichGeometries();
const {
  countryId,
  localityId,
  countryOptions,
  localityOptions,
  loadingLocalities,
  error: optionsError,
  prefill,
  onCountryChange,
} = useLocalityPicker();

const file = ref<File | null>(null);
// El backend lee `properties[name_field]` de cada Feature; por defecto "name".
const nameField = ref("name");
const result = ref<BulkGeometriesResult | null>(null);

const submittable = computed(
  () =>
    localityId.value !== "" &&
    file.value !== null &&
    nameField.value.trim() !== "" &&
    !saving.value
);

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    file.value = null;
    result.value = null;
    nameField.value = "name";
    reset();
    prefill(props.initialCountryId, props.initialLocalityId);
  }
);

// Con resultado ya hubo cambios: cerrar también recarga la tabla.
function onDismiss() {
  if (saving.value) return;
  if (result.value) emit("confirm");
  else emit("close");
}

const onSave = async () => {
  if (!submittable.value || !file.value) return;
  result.value = await upload(
    localityId.value,
    file.value,
    nameField.value.trim()
  );
};
</script>
