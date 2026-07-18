<template>
  <div
    class="bg-white rounded-2xl border border-brand-divider p-12 text-center"
  >
    <div
      v-if="$slots.icon"
      class="w-16 h-16 bg-brand-bg rounded-full flex items-center justify-center mx-auto mb-4"
    >
      <slot name="icon" />
    </div>
    <h3 class="text-brand-text font-semibold text-lg mb-2">
      {{ title }}
    </h3>
    <p class="text-brand-muted text-sm mb-6">
      {{ description }}
    </p>
    <slot />
  </div>
</template>

<script lang="ts" setup>
defineProps<{
  title: string;
  description: string;
}>();
</script>
