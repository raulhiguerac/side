<template>
  <AdminFormModal
    :open="isOpen"
    :icon="Upload"
    :title="replacing ? 'Reemplazar geometría' : 'Cargar geometría'"
    :subtitle="neighborhood?.name"
    submit-label="Subir"
    saving-label="Subiendo…"
    :saving="saving"
    :can-submit="file !== null"
    :error="error"
    @close="$emit('close')"
    @submit="onSave"
  >
    <div class="mb-6">
      <FileUploadField
        v-model="file"
        :extensions="GEOMETRY_UPLOAD.extensions"
        :max-size-mb="GEOMETRY_UPLOAD.maxSizeMb"
        :requirements="GEOMETRY_UPLOAD.requirements"
        :disabled="saving"
        @update:model-value="reset"
      />
      <p v-if="replacing" class="text-brand-muted mt-2 text-xs">
        La geometría actual se reemplaza por la del archivo.
      </p>
    </div>
  </AdminFormModal>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { Upload } from "@lucide/vue";
import AdminFormModal from "@/components/admin/shared/AdminFormModal.vue";
import FileUploadField from "@/components/admin/shared/FileUploadField.vue";
import { useReplaceNeighborhoodGeometry } from "@/composables/admin/useReplaceNeighborhoodGeometry";
import { GEOMETRY_UPLOAD } from "@/constants/catalogUploads";
import type { NeighborhoodAdminDetail } from "@/types/admin/catalog";

const { saving, error, replace, reset } = useReplaceNeighborhoodGeometry();

const props = defineProps<{ neighborhood: NeighborhoodAdminDetail | null }>();

const emit = defineEmits<{ close: []; confirm: [] }>();

const isOpen = computed(() => props.neighborhood !== null);
const replacing = computed(() => props.neighborhood?.geometry != null);

const file = ref<File | null>(null);

// Al reabrir no debe quedar el archivo ni el error de la vez anterior.
watch(
  () => props.neighborhood,
  () => {
    file.value = null;
    reset();
  }
);

const onSave = async () => {
  const neighborhood = props.neighborhood;
  if (!neighborhood || !file.value) return;

  const updated = await replace(neighborhood.id, file.value);
  if (updated) emit("confirm");
};
</script>
