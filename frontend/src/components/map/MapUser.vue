<template>
  <l-map
    v-model:zoom="zoom"
    v-model:center="center"
    @moveend="onMoveEnd"
    :min-zoom="14"
    :max-zoom="17"
  >
    <l-tile-layer
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      layer-type="base"
      name="OpenStreetMap"
    ></l-tile-layer>
    <l-marker
      v-for="marker in props.markers"
      :key="marker.id"
      :lat-lng="[marker.lat, marker.lon]"
    >
      <l-icon
        class-name="!bg-transparent !border-0 !shadow-none"
        :icon-size="marker.id === props.hoveredId ? [48, 48] : [24, 24]"
        :icon-anchor="marker.id === props.hoveredId ? [24, 48] : [12, 24]"
      >
        <component
          v-if="marker.imageType === 'house' || marker.imageType === 'subject'"
          :is="markerIconMap[marker.imageType]"
          :size="marker.id === props.hoveredId ? 48 : 24"
          color="#FFFFFF"
          :fill="marker.id === props.hoveredId ? '#22C55E' : '#1e3a5f'"
        />
        <div
          v-else
          class="rounded-full flex items-center justify-center transition-all"
          :class="
            marker.id === props.hoveredId
              ? 'w-12 h-12 bg-brand-primary'
              : 'w-6 h-6 bg-[#1e3a5f]'
          "
        >
          <component
            :is="markerIconMap[marker.imageType]"
            :size="marker.id === props.hoveredId ? 28 : 14"
            color="#FFFFFF"
          />
        </div>
      </l-icon>
    </l-marker>
    <slot></slot>
  </l-map>
</template>

<script lang="ts" setup>
import { LMarker, LTileLayer, LMap, LIcon } from "@vue-leaflet/vue-leaflet";
import type { MarkerData } from "@/types/maps";
import { markerIconMap } from "@/constants/markerIcons";
import type { LeafletEvent } from "leaflet";

const zoom = defineModel<number>("zoom", { default: 15 });
const center = defineModel<[number, number]>("center")

const props = defineProps<{
  markers: Array<MarkerData>;
  hoveredId: string | null;
}>();

const emit = defineEmits<{
  bbox: [
    payload: {
      min_lat: number;
      max_lat: number;
      min_lon: number;
      max_lon: number;
      zoom: number;
    }
  ];
}>();

function onMoveEnd(event: LeafletEvent) {
  const bounds = event.target.getBounds();
  emit("bbox", {
    min_lat: bounds.getSouth(),
    max_lat: bounds.getNorth(),
    min_lon: bounds.getWest(),
    max_lon: bounds.getEast(),
    zoom: zoom.value,
  });
}
</script>
