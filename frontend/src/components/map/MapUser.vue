<template>
  <l-map v-model:zoom="zoom" :center="props.center">
    <l-tile-layer
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      layer-type="base"
      name="OpenStreetMap"
    ></l-tile-layer>
    <l-marker v-for="marker in props.markers" :key="marker.id" :lat-lng="[marker.lat, marker.lon]">
      <l-icon :icon-size="[32, 32]" :icon-anchor="[16, 32]">
        <img :src="`/icons/${marker.imageType}.svg`" alt="" />
      </l-icon>
    </l-marker>
    <slot></slot>
  </l-map>
</template>

<script lang="ts" setup>
import { LMarker, LTileLayer, LMap, LIcon } from "@vue-leaflet/vue-leaflet";
import type { MarkerData } from "@/types/maps";

const zoom = defineModel<number>("zoom", { default: 15 });

const props = defineProps<{
  center: [number,number];
  markers: Array<MarkerData>;
}>();
</script>
