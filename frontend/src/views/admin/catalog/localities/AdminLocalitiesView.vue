<template>
  <EmptyState
    title="Localidades"
    description="En construcción: falta el listado admin de catalog-service."
  >
    <template #icon>
      <MapIcon class="w-8 h-8 text-brand-muted" />
    </template>
  </EmptyState>
</template>

<script lang="ts" setup>
import { MapIcon } from "@lucide/vue";
import EmptyState from "@/components/shared/EmptyState.vue";
</script>
