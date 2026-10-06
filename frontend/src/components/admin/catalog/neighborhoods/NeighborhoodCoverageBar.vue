<template>
  <div class="rounded-2xl border border-brand-divider bg-white px-5 py-3">
    <div class="mb-2 flex items-baseline justify-between text-sm">
      <span class="text-brand-text font-semibold">Cobertura de geometrías</span>
      <span class="text-brand-muted tabular-nums">
        {{ coverage.with_geometry.toLocaleString("es-CO") }} de
        {{ coverage.total.toLocaleString("es-CO") }} · {{ percent }} %
      </span>
    </div>
    <div class="h-2 overflow-hidden rounded-full bg-brand-divider">
      <div
        class="h-full rounded-full bg-brand-primary transition-all"
        :style="{ width: `${percent}%` }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { NeighborhoodCoverage } from "@/types/admin/catalog";

const props = defineProps<{ coverage: NeighborhoodCoverage }>();

const percent = computed(() =>
  props.coverage.total
    ? Math.round((props.coverage.with_geometry / props.coverage.total) * 100)
    : 0
);
</script>
