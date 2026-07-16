<template>
  <BaseModal :model-value="modelValue" size="3xl" @update:model-value="close">
    <h3 class="text-brand-text font-bold text-lg mb-4">Eliminar fotos</h3>

    <div class="grid grid-cols-5 gap-3">
      <div
        v-for="(image, i) in images"
        :key="image.id"
        :class="[
          'relative aspect-square transition-opacity',
          selectedIds.includes(image.id) ? 'opacity-40' : '',
        ]"
      >
        <img
          :src="image.url"
          :alt="`Foto ${i + 1}`"
          class="w-full h-full object-cover rounded-xl border border-brand-divider"
        />
        <button
          @click="selectImage(image.id)"
          class="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-white shadow border border-brand-border flex items-center justify-center hover:bg-red-50 transition-colors"
        >
          <Trash2 class="w-3.5 h-3.5 text-red-600" />
        </button>
      </div>
    </div>

    <p v-if="error" class="text-sm text-red-600 mt-3">{{ error }}</p>

    <div class="flex gap-3 mt-6">
      <button
        @click="close"
        class="flex-1 py-3 rounded-xl text-sm font-semibold text-brand-text hover:bg-brand-bg transition-colors"
      >
        Cancelar
      </button>
      <button
        @click="handleDelete"
        :disabled="selectedIds.length === 0 || loading"
        class="flex-1 py-3 bg-red-500 text-white rounded-xl text-sm font-semibold hover:bg-red-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {{ loading ? "Eliminando..." : `Eliminar (${selectedIds.length})` }}
      </button>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import { ref, watch } from "vue";
import { Trash2 } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import type { PropertyImageCard } from "@/types/feed";

const props = defineProps<{
  modelValue: boolean;
  propertyId: string;
  images: PropertyImageCard[];
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "success"): void;
}>();

const selectedIds = ref<string[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

watch(
  () => props.modelValue,
  (open) => {
    if (!open) {
      selectedIds.value = [];
      error.value = null;
    }
  }
);

function selectImage(id: string) {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter(
      (selectedId) => selectedId !== id
    );
    return;
  }
  selectedIds.value = [...selectedIds.value, id];
}

async function handleDelete() {
  if (loading.value) return;
  loading.value = true;
  error.value = null;
  try {
    await propertiesApi.delete(PROPERTIES_ENDPOINTS.images(props.propertyId), {
      data: { image_ids: selectedIds.value },
    });
    emit("success");
    close();
  } catch {
    error.value = "No se pudieron eliminar las fotos";
  } finally {
    loading.value = false;
  }
}

function close() {
  emit("update:modelValue", false);
}
</script>
