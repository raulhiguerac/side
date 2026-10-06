<template>
  <div
    v-if="total"
    class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-between"
  >
    <p class="text-brand-muted text-sm">
      Mostrando {{ range.from }}-{{ range.to }} de {{ formatNumber(total) }}
    </p>
    <PaginationArrows
      :has-prev="hasPrev"
      :has-next="hasNext"
      @prev="$emit('prev')"
      @next="$emit('next')"
    />
  </div>
</template>

<script lang="ts" setup>
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import type { PageRange } from "@/types/pagination";
import { formatNumber } from "@/utils/number";

defineProps<{
  range: PageRange;
  total: number;
  hasPrev: boolean;
  hasNext: boolean;
}>();

defineEmits<{ prev: []; next: [] }>();
</script>
