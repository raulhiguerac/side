<template>
  <span
    :class="[
      'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
      active
        ? 'bg-brand-primary-light text-green-700'
        : 'bg-gray-100 text-brand-muted',
    ]"
  >
    {{ active ? "Activo" : "Inactivo" }}
  </span>
</template>

<script setup lang="ts">
defineProps<{ active: boolean }>();
</script>
