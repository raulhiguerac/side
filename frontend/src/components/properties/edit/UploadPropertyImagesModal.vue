<template>
  <BaseModal :model-value="modelValue" size="3xl" @update:model-value="close">
    <h3 class="text-brand-text font-bold text-lg mb-4">Agregar fotos</h3>

    <StepImagenes
      v-model="selectedFiles"
      :max="imagesAllowed"
      :has-existing-photos="hasExistingPhotos"
    />

    <p v-if="error" class="text-sm text-red-600 mt-3">{{ error }}</p>

    <div class="flex gap-3 mt-6">
      <BaseButton variant="ghost" size="lg" @click="close" class="flex-1">
        Cancelar
      </BaseButton>
      <BaseButton
        size="lg"
        @click="handleUpload"
        :disabled="selectedFiles.length === 0"
        :loading="loading"
        class="flex-1"
      >
        {{ loading ? "Subiendo..." : "Subir fotos" }}
      </BaseButton>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { ref, watch } from "vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import StepImagenes from "@/components/properties/create/StepImagenes.vue";
import { useImageUpload } from "@/composables/properties/useImageUpload";

const props = defineProps<{
  modelValue: boolean;
  propertyId: string;
  imagesAllowed: number;
  hasExistingPhotos: boolean;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "success"): void;
}>();

const selectedFiles = ref<File[]>([]);
const { loading, error, uploadImages } = useImageUpload();

watch(
  () => props.modelValue,
  (open) => {
    if (!open) {
      selectedFiles.value = [];
      error.value = null;
    }
  }
);

function close() {
  emit("update:modelValue", false);
}

async function handleUpload() {
  const success = await uploadImages(selectedFiles.value, props.propertyId);
  if (success) {
    emit("success");
    close();
  }
}
</script>
