<template>
  <BaseModal
    size="3xl"
    :model-value="props.isOpen"
    @update:model-value="$emit('close')"
  >
    <div class="relative flex items-center">
      <IconButton
        label="Foto anterior"
        variant="surface"
        size="lg"
        @click="
          currentSlide =
            currentSlide === 0 ? props.images.length - 1 : currentSlide - 1
        "
        class="absolute left-0 z-10"
      >
        <ChevronLeft :size="18" />
      </IconButton>

      <Carousel v-model="currentSlide" :wrap-around="true" class="w-full">
        <Slide v-for="(img, i) in props.images" :key="i">
          <img
            :src="img.url"
            :alt="`Foto ${i + 1}`"
            class="w-full max-h-[70vh] object-contain"
          />
        </Slide>
      </Carousel>

      <IconButton
        label="Foto siguiente"
        variant="surface"
        size="lg"
        @click="
          currentSlide =
            currentSlide === props.images.length - 1 ? 0 : currentSlide + 1
        "
        class="absolute right-0 z-10"
      >
        <ChevronRight :size="18" />
      </IconButton>
    </div>
  </BaseModal>
</template>

<script setup lang="ts">
import IconButton from "@/components/shared/IconButton.vue";
import { ref, watch } from "vue";
import { Carousel, Slide } from "vue3-carousel";
import "vue3-carousel/dist/carousel.css";
import { ChevronLeft, ChevronRight } from "@lucide/vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import type { PropertyImageCard } from "@/types/properties/images";

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
