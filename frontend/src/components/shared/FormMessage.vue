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
  error: "border-brand-danger-border bg-brand-danger-light text-brand-danger",
  success:
    "border-brand-success-border bg-brand-success-light text-brand-success",
};
</script>
