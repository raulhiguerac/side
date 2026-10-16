<template>
  <AdminFormModal
    :open="open"
    :icon="FileUp"
    title="Subir barrios"
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
        { label: 'Barrios guardados', value: result.created },
        { label: 'Con error', value: result.errors.length },
      ]"
      issues-title="No se guardaron"
      :issues="result.errors"
    />
    <div v-else class="mb-6 space-y-4">
      <CascadeSelectFields
        v-model="place"
        id-prefix="bulk-neighborhoods"
        :fields="CASCADE"
        :disabled="saving"
      />

      <FileUploadField
        v-model="file"
        :extensions="BULK_NEIGHBORHOODS_UPLOAD.extensions"
        :max-size-mb="BULK_NEIGHBORHOODS_UPLOAD.maxSizeMb"
        :requirements="BULK_NEIGHBORHOODS_UPLOAD.requirements"
        :disabled="saving"
        @update:model-value="reset"
      />
    </div>

    <template v-if="result" #footer>
      <button
        type="button"
        class="bg-brand-primary w-full rounded-xl py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90"
        @click="$emit('confirm')"
      >
        Listo
      </button>
    </template>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { FileUp } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import CascadeSelectFields from "@/components/admin/shared/CascadeSelectFields.vue";
import { COUNTRY_SELECT, LOCALITY_SELECT } from "@/constants/catalogFilters";
import FileUploadField from "@/components/admin/shared/FileUploadField.vue";
import BulkResultSummary from "@/components/admin/catalog/neighborhoods/widgets/BulkResultSummary.vue";
import { useBulkCreateNeighborhoods } from "@/composables/admin/useBulkCreateNeighborhoods";
import { BULK_NEIGHBORHOODS_UPLOAD } from "@/constants/catalogUploads";
import type { BulkNeighborhoodsResult } from "@/types/admin/catalog";

const props = defineProps<{
  open: boolean;
  initialCountryId: string | null;
  initialLocalityId: string | null;
}>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const { saving, error, upload, reset } = useBulkCreateNeighborhoods();
const CASCADE = [COUNTRY_SELECT, LOCALITY_SELECT];
const place = ref<Record<string, string>>({});
const localityId = computed(() => place.value.locality_id ?? "");

const file = ref<File | null>(null);
const result = ref<BulkNeighborhoodsResult | null>(null);

const canSubmit = computed(
  () => localityId.value !== "" && file.value !== null
);

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    file.value = null;
    result.value = null;
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
  result.value = await upload(localityId.value, file.value);
};
</script>
