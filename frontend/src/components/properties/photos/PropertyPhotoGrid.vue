<template>
  <div
    class="grid grid-cols-4 grid-rows-[200px_200px] gap-[6px] rounded-2xl overflow-hidden"
  >
    <div
      v-for="(img, i) in gridImages"
      :key="i"
      :class="`cell-${i + 1}`"
      class="overflow-hidden group cursor-pointer"
      @click="openPopup(i)"
    >
      <img
        :src="img.url"
        :alt="`Foto ${i + 1}`"
        class="w-full h-full object-cover transition-transform duration-200 group-hover:scale-[1.03]"
      />
    </div>
  </div>

  <PhotoGalleryPopup
    :is-open="isOpen"
    :images="allImages"
    :start-index="imageIndex"
    @close="isOpen = false"
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { PropertyImageCard } from "@/types/feed";
import PhotoGalleryPopup from "@/components/properties/photos/PhotoGalleryPopup.vue";

const isOpen= ref<boolean>(false);
const imageIndex= ref<number>(0);

const { gridImages, allImages } = defineProps<{
  gridImages: Array<PropertyImageCard>;
  allImages: Array<PropertyImageCard>;
}>();

function openPopup(i: number){
  isOpen.value = true
  imageIndex.value = i
}
</script>

<style scoped>
/* grid-area no tiene equivalente limpio en Tailwind arbitrary values con v-for dinámico */
.cell-1 {
  grid-area: 1 / 1 / 3 / 3;
}
.cell-2 {
  grid-area: 1 / 3 / 2 / 4;
}
.cell-3 {
  grid-area: 1 / 4 / 2 / 5;
}
.cell-4 {
  grid-area: 2 / 3 / 3 / 4;
}
.cell-5 {
  grid-area: 2 / 4 / 3 / 5;
}
</style>
