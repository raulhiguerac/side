<template>
  <button
    :disabled="disabled || loading"
    :class="[
      'bg-brand-primary inline-flex items-center justify-center gap-2 rounded-xl font-semibold text-white transition-colors hover:bg-green-600 disabled:cursor-not-allowed disabled:bg-brand-primary-light disabled:text-brand-placeholder',
      SIZE_CLASSES[size],
    ]"
  >
    <BaseSpinner v-if="loading" class="h-4 w-4" />
    <slot />
  </button>
</template>

<script lang="ts" setup>
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import type { ButtonSize } from "@/types/shared/ui";

withDefaults(
  defineProps<{ disabled?: boolean; loading?: boolean; size?: ButtonSize }>(),
  { disabled: false, loading: false, size: "md" }
);

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: "px-4 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "h-12 px-5 text-base",
};
</script>
