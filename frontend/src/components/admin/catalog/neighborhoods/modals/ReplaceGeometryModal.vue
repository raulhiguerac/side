<template>
  <BaseModal :model-value="isOpen" @update:model-value="$emit('close')">
    <div class="mb-4 flex items-center gap-4">
      <div
        class="bg-brand-primary-light flex h-12 w-12 items-center justify-center rounded-xl"
      >
        <Upload class="text-brand-primary h-6 w-6" />
      </div>
      <div class="min-w-0">
        <h3 class="text-brand-text text-lg font-bold">
          {{ replacing ? "Reemplazar geometría" : "Cargar geometría" }}
        </h3>
        <p v-if="neighborhood" class="text-brand-muted truncate text-sm">
          {{ neighborhood.name }}
        </p>
      </div>
    </div>

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

    <FormMessage v-if="error" variant="error" class="mb-4">
      {{ error }}
    </FormMessage>

    <div class="flex gap-3">
      <button
        type="button"
        :disabled="saving"
        class="text-brand-text hover:bg-brand-bg flex-1 rounded-xl py-3 text-sm font-semibold transition-colors disabled:opacity-50"
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
  </BaseModal>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { Upload } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
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
const submittable = computed(() => file.value !== null && !saving.value);

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
