<template>
  <div class="text-xs leading-snug">
    <strong>{{ marker.label }}</strong>
    <div v-if="marker.categoryLabel">{{ marker.categoryLabel }}</div>
    <div v-if="marker.address">{{ marker.address }}</div>
    <div v-if="marker.phone">{{ marker.phone }}</div>
    <a
      v-if="safeWebsite"
      :href="safeWebsite"
      target="_blank"
      rel="noopener noreferrer"
    >
      {{ marker.website }}
    </a>
  </div>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import type { MarkerData } from "@/types/maps/base";

const props = defineProps<{ marker: MarkerData }>();

// El sitio viene de datos externos: solo enlaces http(s), nunca `javascript:`.
const safeWebsite = computed(() =>
  /^https?:\/\//i.test(props.marker.website ?? "")
    ? props.marker.website
    : undefined
);
</script>
