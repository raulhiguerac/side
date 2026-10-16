<template>
  <AdminFormModal
    :open="open"
    :icon="MapPinned"
    title="Subir geometrías"
    submit-label="Subir"
    saving-label="Subiendo…"
    :saving="saving"
    :can-submit="canSubmit"
    :error="error"
    @close="onDismiss"
    @submit="onSave"
  >
    <BulkResultSummary
      v-if="result"
      class="mb-6"
      :stats="[
        { label: 'Geometrías actualizadas', value: result.updated },
        { label: 'Barrios sin geometría', value: result.unmatched.length },
      ]"
      issues-title="Barrios de la localidad sin Feature"
      :issues="result.unmatched"
    />
    <div v-else class="mb-6 space-y-4">
      <CascadeSelectFields
        v-model="place"
        id-prefix="bulk-geometries"
        :fields="CASCADE"
        :disabled="saving"
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

    <template v-if="result" #footer>
      <BaseButton size="lg" block @click="$emit('confirm')"> Listo </BaseButton>
    </template>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { computed, ref, watch } from "vue";
import { MapPinned } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import CascadeSelectFields from "@/components/admin/shared/CascadeSelectFields.vue";
import { COUNTRY_SELECT, LOCALITY_SELECT } from "@/constants/catalogFilters";
import FileUploadField from "@/components/admin/shared/FileUploadField.vue";
import BulkResultSummary from "@/components/admin/catalog/neighborhoods/widgets/BulkResultSummary.vue";
import { useBulkEnrichGeometries } from "@/composables/admin/useBulkEnrichGeometries";
import { BULK_GEOMETRIES_UPLOAD } from "@/constants/catalogUploads";
import type { BulkGeometriesResult } from "@/types/admin/catalog";

const props = defineProps<{
  open: boolean;
  initialCountryId: string | null;
  initialLocalityId: string | null;
}>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const { saving, error, upload, reset } = useBulkEnrichGeometries();
const CASCADE = [COUNTRY_SELECT, LOCALITY_SELECT];
const place = ref<Record<string, string>>({});
const localityId = computed(() => place.value.locality_id ?? "");

const file = ref<File | null>(null);
// El backend lee `properties[name_field]` de cada Feature; por defecto "name".
const nameField = ref("name");
const result = ref<BulkGeometriesResult | null>(null);

const canSubmit = computed(
  () =>
    localityId.value !== "" &&
    file.value !== null &&
    nameField.value.trim() !== ""
);

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    file.value = null;
    result.value = null;
    nameField.value = "name";
    reset();
    place.value = {
      country_id: props.initialCountryId ?? "",
      locality_id: props.initialLocalityId ?? "",
    };
  }
);

// Con resultado ya hubo cambios: cerrar también recarga la tabla.
function onDismiss() {
  if (saving.value) return;
  if (result.value) emit("confirm");
  else emit("close");
}

const onSave = async () => {
  if (!canSubmit.value || !file.value) return;
  result.value = await upload(
    localityId.value,
    file.value,
    nameField.value.trim()
  );
};
</script>
