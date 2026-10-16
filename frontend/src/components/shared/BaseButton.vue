<template>
  <component
    :is="to ? RouterLink : 'button'"
    :to="to"
    :type="to ? undefined : type"
    :disabled="to ? undefined : disabled || loading"
    :class="[
      'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/40 disabled:cursor-not-allowed disabled:opacity-50',
      VARIANT_CLASSES[variant],
      variant === 'link' ? 'text-sm' : SIZE_CLASSES[size],
      { 'w-full': block },
    ]"
  >
    <BaseSpinner v-if="loading" class="h-4 w-4" />
    <slot />
  </component>
</template>

<script lang="ts" setup>
import { RouterLink, type RouteLocationRaw } from "vue-router";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import type { ButtonSize, ButtonVariant } from "@/types/shared/ui";

// `type="button"` por defecto: un botón dentro de un <form> no lo envía sin pedirlo.
// Con `to` se dibuja como RouterLink: un link con aspecto de botón.
withDefaults(
  defineProps<{
    variant?: ButtonVariant;
    size?: ButtonSize;
    type?: "button" | "submit";
    disabled?: boolean;
    loading?: boolean;
    block?: boolean;
    to?: RouteLocationRaw;
  }>(),
  {
    variant: "primary",
    size: "md",
    type: "button",
    disabled: false,
    loading: false,
    block: false,
    to: undefined,
  }
);

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-primary-strong text-white hover:bg-brand-primary-strong-hover",
  secondary:
    "border border-brand-border bg-white text-brand-text hover:bg-brand-bg",
  ghost: "text-brand-text hover:bg-brand-bg",
  danger: "bg-brand-danger text-white hover:bg-brand-danger-hover",
  "danger-soft":
    "border border-brand-danger-border bg-white text-brand-danger hover:bg-brand-danger-light",
  link: "text-brand-primary-strong hover:underline",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-3 text-sm",
  xl: "h-12 px-6 text-base",
};
</script>
