<template>
  <BaseModal :model-value="open" @update:model-value="onDismiss">
    <div class="mb-4 flex items-center gap-4">
      <div
        class="bg-brand-primary-light flex h-12 w-12 items-center justify-center rounded-xl"
      >
        <FileUp class="text-brand-primary h-6 w-6" />
      </div>
      <h3 class="text-brand-text text-lg font-bold">Subir barrios</h3>
    </div>

    <template v-if="result">
      <BulkResultSummary
        class="mb-6"
        :stats="[
          { label: 'Barrios guardados', value: result.created },
          { label: 'Con error', value: result.errors.length },
        ]"
        issues-title="No se guardaron"
        :issues="result.errors"
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
          id-prefix="bulk-neighborhoods"
          :country-options="countryOptions"
          :locality-options="localityOptions"
          :loading-localities="loadingLocalities"
          :disabled="saving"
          @country-change="onCountryChange"
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
import { FileUp } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import FileUploadField from "@/components/admin/shared/FileUploadField.vue";
import BulkResultSummary from "@/components/admin/catalog/neighborhoods/widgets/BulkResultSummary.vue";
import LocalitySelectFields from "@/components/admin/catalog/neighborhoods/widgets/LocalitySelectFields.vue";
import { useBulkCreateNeighborhoods } from "@/composables/admin/useBulkCreateNeighborhoods";
import { useLocalityPicker } from "@/composables/admin/useLocalityPicker";
import { BULK_NEIGHBORHOODS_UPLOAD } from "@/constants/catalogUploads";
import type { BulkNeighborhoodsResult } from "@/types/admin/catalog";

const props = defineProps<{
  open: boolean;
  initialCountryId: string | null;
  initialLocalityId: string | null;
}>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const { saving, error, upload, reset } = useBulkCreateNeighborhoods();
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
const result = ref<BulkNeighborhoodsResult | null>(null);

const submittable = computed(
  () => localityId.value !== "" && file.value !== null && !saving.value
);

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    file.value = null;
    result.value = null;
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
  result.value = await upload(localityId.value, file.value);
};
</script>
