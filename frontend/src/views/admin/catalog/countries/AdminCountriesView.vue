<template>
  <EmptyState
    title="Países"
    description="En construcción: falta el listado admin de catalog-service."
  >
    <template #icon>
      <Flag class="w-8 h-8 text-brand-muted" />
    </template>
  </EmptyState>
</template>

<script lang="ts" setup>
import { Flag } from "@lucide/vue";
import EmptyState from "@/components/shared/EmptyState.vue";
</script>
