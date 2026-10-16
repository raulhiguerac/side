<template>
  <div class="h-72 overflow-hidden rounded-xl border border-brand-divider">
    <l-map :zoom="ZOOM" :center="center" :options="MAP_OPTIONS">
      <l-tile-layer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        layer-type="base"
        name="OpenStreetMap"
      />
      <l-marker :lat-lng="center">
        <l-icon class-name="" :icon-size="[28, 28]" :icon-anchor="[14, 28]">
          <MapPin :size="28" color="white" :fill="BRAND_COLORS.primary" />
        </l-icon>
      </l-marker>
    </l-map>
  </div>
</template>

<script setup lang="ts">
import { LIcon, LMap, LMarker, LTileLayer } from "@vue-leaflet/vue-leaflet";
import type * as L from "leaflet";
import { MapPin } from "@lucide/vue";
import { BRAND_COLORS } from "@/constants/brandColors";

defineProps<{ center: [number, number] }>();

/** Escala de ciudad: la localidad es un punto, no un polígono que encuadrar. */
const ZOOM = 11;

const MAP_OPTIONS: L.MapOptions = {
  zoomControl: false,
  dragging: false,
  scrollWheelZoom: false,
  doubleClickZoom: false,
  boxZoom: false,
  keyboard: false,
  touchZoom: false,
};
</script>
