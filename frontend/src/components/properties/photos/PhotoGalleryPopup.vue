<template>
  <BaseModal
    size="3xl"
    :model-value="props.isOpen"
    @update:model-value="$emit('close')"
  >
    <div class="relative flex items-center">
      <button
        class="absolute left-0 z-10 w-9 h-9 rounded-full bg-white/90 hover:bg-white flex items-center justify-center"
        @click="
          currentSlide =
            currentSlide === 0 ? props.images.length - 1 : currentSlide - 1
        "
      >
        <ChevronLeft :size="18" />
      </button>

      <Carousel v-model="currentSlide" :wrap-around="true" class="w-full">
        <Slide v-for="(img, i) in props.images" :key="i">
          <img
            :src="img.url"
            :alt="`Foto ${i + 1}`"
            class="w-full max-h-[70vh] object-contain"
          />
        </Slide>
      </Carousel>

      <button
        class="absolute right-0 z-10 w-9 h-9 rounded-full bg-white/90 hover:bg-white flex items-center justify-center"
        @click="
          currentSlide =
            currentSlide === props.images.length - 1 ? 0 : currentSlide + 1
        "
      >
        <ChevronRight :size="18" />
      </button>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { Carousel, Slide } from "vue3-carousel";
import "vue3-carousel/dist/carousel.css";
import { ChevronLeft, ChevronRight } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import type { PropertyImageCard } from "@/types/feed";

const props = defineProps<{
  isOpen: boolean;
  images: PropertyImageCard[];
  startIndex: number;
}>();

defineEmits<{ close: [] }>();

const currentSlide = ref(props.startIndex);

watch(
  () => props.startIndex,
  (i) => {
    currentSlide.value = i;
  }
);
</script>

<style scoped></style>
