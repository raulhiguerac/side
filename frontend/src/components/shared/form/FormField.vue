<template>
  <div>
    <label
      :for="inputId"
      class="text-brand-text mb-1 block text-sm font-medium"
    >
      {{ label }}
    </label>
    <slot />
    <p v-if="error" class="text-brand-danger mt-1 text-xs">{{ error }}</p>
    <p v-else-if="hint" class="text-brand-muted mt-1 text-xs">{{ hint }}</p>
  </div>
</template>

<script lang="ts" setup>
// Label + campo + error o ayuda; el `id` del campo lo pone quien lo usa y llega acá como `inputId`.
defineProps<{
  label: string;
  inputId: string;
  hint?: string;
  error?: string | null;
}>();
</script>
