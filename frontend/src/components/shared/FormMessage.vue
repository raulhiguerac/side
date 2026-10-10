<template>
  <p
    role="alert"
    :class="['rounded-xl border px-3 py-2 text-sm', VARIANT_CLASSES[variant]]"
  >
    <slot />
  </p>
</template>

<script lang="ts" setup>
import type { MessageVariant } from "@/types/shared/ui";

defineProps<{ variant: MessageVariant }>();

const VARIANT_CLASSES: Record<MessageVariant, string> = {
  error: "border-red-200 bg-red-50 text-red-600",
  success: "border-green-200 bg-green-50 text-green-700",
};
</script>
