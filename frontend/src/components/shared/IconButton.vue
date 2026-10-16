<template>
  <button
    type="button"
    :aria-label="label"
    :title="label"
    :class="[
      'inline-flex shrink-0 items-center justify-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/40 disabled:cursor-not-allowed disabled:opacity-50',
      SIZE_CLASSES[size],
      VARIANT_CLASSES[variant],
      danger
        ? 'hover:bg-red-50 hover:text-red-600'
        : variant === 'plain'
        ? 'hover:bg-brand-bg hover:text-brand-text'
        : 'hover:bg-white',
    ]"
  >
    <slot />
  </button>
</template>

<script lang="ts" setup>
import type { IconButtonSize, IconButtonVariant } from "@/types/shared/ui";

// `label` es obligatorio: un botón de solo icono no puede quedar sin nombre accesible.
withDefaults(
  defineProps<{
    label: string;
    variant?: IconButtonVariant;
    size?: IconButtonSize;
    danger?: boolean;
  }>(),
  { variant: "plain", size: "md", danger: false }
);

const SIZE_CLASSES: Record<IconButtonSize, string> = {
  xs: "h-5 w-5 rounded-full text-sm",
  sm: "h-6 w-6 rounded-full",
  md: "h-8 w-8 rounded-lg",
  lg: "h-9 w-9 rounded-full",
};

const VARIANT_CLASSES: Record<IconButtonVariant, string> = {
  surface: "border border-brand-border bg-white/90 text-brand-muted shadow-sm",
  plain: "text-brand-muted",
};
</script>
