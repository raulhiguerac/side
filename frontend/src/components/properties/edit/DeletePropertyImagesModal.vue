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
        <IconButton
          label="Marcar foto para eliminar"
          variant="surface"
          size="sm"
          danger
          @click="selectImage(image.id)"
          class="absolute right-1.5 top-1.5"
        >
          <Trash2 class="w-3.5 h-3.5 text-brand-danger" />
        </IconButton>
      </div>
    </div>

    <p v-if="error" class="text-sm text-brand-danger mt-3">{{ error }}</p>

    <div class="flex gap-3 mt-6">
      <BaseButton variant="ghost" size="lg" @click="close" class="flex-1">
        Cancelar
      </BaseButton>
      <BaseButton
        variant="danger"
        size="lg"
        @click="handleDelete"
        :disabled="selectedIds.length === 0 || loading"
        class="flex-1"
      >
        {{ loading ? "Eliminando..." : `Eliminar (${selectedIds.length})` }}
      </BaseButton>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import IconButton from "@/components/shared/IconButton.vue";
import { ref, watch } from "vue";
import { Trash2 } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import * as propertiesApi from "@/api/properties";
import type { PropertyImageCard } from "@/types/properties/images";

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
    await propertiesApi.deleteImages(props.propertyId, selectedIds.value);
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
