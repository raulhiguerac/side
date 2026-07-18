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
      <button
        @click="$emit('close')"
        class="flex-1 py-3 rounded-xl text-sm font-semibold text-brand-text hover:bg-brand-bg transition-colors"
      >
        Cancelar
      </button>
      <button
        @click="handleDelete"
        :disabled="isDeleting"
        class="flex-1 py-3 bg-red-500 text-white rounded-xl text-sm font-semibold hover:bg-red-600 transition-colors"
      >
        {{ isDeleting ? "Eliminando..." : "Eliminar" }}
      </button>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import { ref, computed } from "vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";

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
    await propertiesApi.delete(PROPERTIES_ENDPOINTS.byId(props.propertyId));
    emit("deleted", props.propertyId);
  } catch (error) {
    console.error("Error al eliminar propiedad:", error);
    alert("Error al eliminar la propiedad");
  } finally {
    isDeleting.value = false;
  }
}
</script>
