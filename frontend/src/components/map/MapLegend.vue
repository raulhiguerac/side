<template>
  <div class="flex items-center gap-3 flex-wrap">
    <div
      v-for="bucket in buckets"
      :key="bucket.key"
      class="flex items-center gap-1.5"
    >
      <span
        class="inline-block w-2.5 h-2.5 rounded-full"
        :style="{ backgroundColor: bucket.color }"
      />
      <span class="text-xs text-brand-muted">{{ bucket.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { MarkerImageType } from "@/types/maps";
import { POI_COLORS, POI_BUCKET_LABELS } from "@/constants/poiColors";

const buckets = computed(() =>
  (Object.keys(POI_COLORS) as MarkerImageType[]).map((key) => ({
    key,
    color: POI_COLORS[key] as string,
    label: POI_BUCKET_LABELS[key] ?? key,
  }))
);
</script>
