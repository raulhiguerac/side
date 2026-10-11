<template>
  <svg
    v-if="svgPath && viewBox"
    :viewBox="viewBox"
    preserveAspectRatio="xMidYMid meet"
    class="h-9 w-9"
    aria-hidden="true"
  >
    <path
      :d="svgPath"
      class="fill-brand-primary-light stroke-brand-primary"
      stroke-width="1.5"
      vector-effect="non-scaling-stroke"
    />
  </svg>
  <span v-else class="text-brand-muted text-xs">Sin geometría</span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  svgPath: string | null;
  bbox: [number, number, number, number] | null;
}>();

/** `ST_AsSVG` invierte la Y, así que el viewBox arranca en `-max_lat`. */
const viewBox = computed(() => {
  if (!props.bbox) return null;
  const [minLon, minLat, maxLon, maxLat] = props.bbox;
  return `${minLon} ${-maxLat} ${maxLon - minLon} ${maxLat - minLat}`;
});
</script>
