<template>
  <EmptyState
    title="Divisiones administrativas"
    description="En construcción: falta el listado admin de catalog-service."
  >
    <template #icon>
      <Landmark class="w-8 h-8 text-brand-muted" />
    </template>
  </EmptyState>
</template>

<script lang="ts" setup>
import { Landmark } from "@lucide/vue";
import EmptyState from "@/components/shared/EmptyState.vue";
</script>
