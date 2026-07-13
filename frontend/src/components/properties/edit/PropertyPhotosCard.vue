<template>
  <div
    class="bg-white rounded-2xl border border-brand-divider p-6 flex-1 flex flex-col"
  >
    <label
      class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3"
    >
      Fotos
    </label>
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
  </div>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import PropertyPhotoGrid from "@/components/properties/photos/PropertyPhotoGrid.vue";
import type { PropertyDetail } from "@/types/properties";

const props = defineProps<{
  property: PropertyDetail | null;
}>();

const allImages = computed(() => props.property?.images ?? []);
const gridImages = computed(() => allImages.value.slice(0, 5));
</script>
