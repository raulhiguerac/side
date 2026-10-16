<template>
  <div class="flex items-center justify-center gap-3">
    <BaseButton :disabled="!hasPrev" @click="$emit('prev')">
      <svg
        class="w-4 h-4"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M15 19l-7-7 7-7"
        />
      </svg>
      Anterior
    </BaseButton>
    <BaseButton :disabled="!hasNext" @click="$emit('next')">
      Siguiente
      <svg
        class="w-4 h-4"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </BaseButton>
  </div>
</template>

<script lang="ts" setup>
import BaseButton from "@/components/shared/BaseButton.vue";
defineProps<{
  hasPrev: boolean;
  hasNext: boolean;
}>();

defineEmits<{
  (e: "prev"): void;
  (e: "next"): void;
}>();
</script>
