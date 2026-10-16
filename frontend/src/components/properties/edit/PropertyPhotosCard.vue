<template>
  <div
    class="bg-white rounded-2xl border border-brand-divider p-6 flex-1 flex flex-col"
  >
    <div class="flex items-center justify-between mb-3">
      <label
        class="text-xs font-semibold text-brand-muted uppercase tracking-wide"
      >
        Fotos
      </label>
      <span class="text-sm font-semibold text-brand-muted">
        <span class="text-base text-brand-primary font-bold">{{
          allImages.length
        }}</span
        >/{{ LIMITS.MAX_IMAGES_PER_PROPERTY }}
      </span>
    </div>
    <PropertyPhotoGrid
      v-if="allImages.length"
      expand
      :grid-images="gridImages"
      :all-images="allImages"
    />
    <div
      v-else
      class="flex-1 min-h-64 rounded-2xl border-2 border-dashed border-brand-border bg-brand-bg flex items-center justify-center text-brand-muted text-xs"
    >
      Esta propiedad no tiene fotos
    </div>

    <div class="grid grid-cols-[20%_25%_10%_25%_20%] mt-4 items-start">
      <div></div>
      <div class="flex flex-col items-center gap-1.5">
        <BaseButton
          @click="emit('add-photos')"
          :disabled="imagesAllowed === 0"
          block
        >
          Agregar fotos
        </BaseButton>
        <p v-if="imagesAllowed === 0" class="text-xs text-brand-danger">
          Primero debes borrar algunas
        </p>
      </div>
      <div></div>
      <BaseButton
        variant="danger-soft"
        @click="emit('delete-photos')"
        :disabled="!allImages.length"
      >
        Eliminar
      </BaseButton>
      <div></div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
import { computed } from "vue";
import PropertyPhotoGrid from "@/components/properties/photos/PropertyPhotoGrid.vue";
import { LIMITS } from "@/config";
import type { PropertyDetail } from "@/types/properties/detail";

const props = defineProps<{
  property: PropertyDetail | null;
}>();

const emit = defineEmits<{
  (e: "add-photos"): void;
  (e: "delete-photos"): void;
}>();

const allImages = computed(() => props.property?.images ?? []);
const gridImages = computed(() => allImages.value.slice(0, 5));
const imagesAllowed = computed(
  () => LIMITS.MAX_IMAGES_PER_PROPERTY - allImages.value.length
);
</script>
