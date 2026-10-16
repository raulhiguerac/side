<template>
  <button
    type="button"
    :aria-pressed="selected"
    :class="[
      'inline-flex items-center justify-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/40 disabled:cursor-not-allowed disabled:opacity-50',
      selected
        ? 'border-brand-primary bg-brand-primary-light text-brand-primary-dark'
        : 'border-brand-border bg-white text-brand-text hover:border-brand-primary/40',
    ]"
  >
    <slot />
  </button>
</template>

<script lang="ts" setup>
// Opción chica elegible (estrato, moneda, días…); el grupo lo arma quien la usa.
defineProps<{ selected: boolean }>();
</script>
