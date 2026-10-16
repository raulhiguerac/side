<template>
  <BaseModal :model-value="isOpen" @update:model-value="$emit('close')">
    <div class="flex items-center gap-4 mb-4">
      <div
        class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          class="text-red-600"
        >
          <path d="M3 6h18" />
          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
        </svg>
      </div>
      <div>
        <h3 class="text-brand-text font-bold text-lg">Eliminar propiedad</h3>
      </div>
    </div>

    <p class="text-brand-muted text-sm mb-6">
      ¿Estás seguro de que deseas eliminar esta propiedad? Esta acción no se
      puede deshacer.
    </p>

    <div class="flex gap-3">
      <BaseButton
        variant="ghost"
        size="lg"
        @click="$emit('close')"
        class="flex-1"
      >
        Cancelar
      </BaseButton>
      <BaseButton
        variant="danger"
        size="lg"
        @click="handleDelete"
        :disabled="isDeleting"
        class="flex-1"
      >
        {{ isDeleting ? "Eliminando..." : "Eliminar" }}
      </BaseButton>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { ref, computed } from "vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import * as propertiesApi from "@/api/properties";
import { logger } from "@/utils/logger";

const props = defineProps<{
  propertyId: string | null;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "deleted", propertyId: string): void;
}>();

const isOpen = computed(() => props.propertyId !== null);
const isDeleting = ref(false);

async function handleDelete() {
  if (!props.propertyId) return;

  isDeleting.value = true;
  try {
    await propertiesApi.deleteProperty(props.propertyId);
    emit("deleted", props.propertyId);
  } catch (error) {
    logger.error("Error al eliminar propiedad:", error);
    alert("Error al eliminar la propiedad");
  } finally {
    isDeleting.value = false;
  }
}
</script>
