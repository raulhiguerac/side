<template>
  <button
    type="button"
    :aria-pressed="selected"
    :class="[
      'rounded-2xl border-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/40 disabled:cursor-not-allowed disabled:opacity-50',
      selected
        ? 'border-brand-primary bg-brand-primary-light'
        : 'border-brand-border bg-white hover:border-brand-primary/40',
    ]"
  >
    <slot />
  </button>
</template>

<script lang="ts" setup>
// Tarjeta elegible: fija el marco y el estado; el contenido y su distribución van en el slot.
defineProps<{ selected: boolean }>();
</script>
