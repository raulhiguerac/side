<template>
  <l-map
    ref="mapRef"
    v-model:zoom="zoom"
    v-model:center="internalCenter"
    @moveend="onMoveEnd"
    @ready="onMapReady"
    :min-zoom="props.minZoom ?? 14"
    :max-zoom="17"
  >
    <l-tile-layer
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      layer-type="base"
      name="OpenStreetMap"
    />

    <!-- Property markers (subject, house, apartment) — declarative with custom icon -->
    <l-marker
      v-for="marker in specialMarkers"
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

    <slot />
  </l-map>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onUnmounted } from "vue";
import { LMarker, LTileLayer, LMap, LIcon } from "@vue-leaflet/vue-leaflet";
import * as L from "leaflet";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { MarkerClusterGroup } = require("leaflet.markercluster");
import type { MarkerData, MarkerImageType } from "@/types/maps";
import { markerIconMap } from "@/constants/markerIcons";
import { POI_COLORS } from "@/constants/poiColors";
import type { LeafletEvent } from "leaflet";

const SPECIAL_TYPES: MarkerImageType[] = ["subject", "house", "apartment"];

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function buildPoiPopupHtml(m: MarkerData): string {
  const rows: string[] = [`<strong>${escapeHtml(m.label ?? "")}</strong>`];
  if (m.categoryLabel) rows.push(escapeHtml(m.categoryLabel));
  if (m.address) rows.push(escapeHtml(m.address));
  if (m.phone) rows.push(escapeHtml(m.phone));
  if (m.website) {
    const safeHref = encodeURI(m.website);
    rows.push(
      `<a href="${safeHref}" target="_blank" rel="noopener noreferrer">${escapeHtml(
        m.website
      )}</a>`
    );
  }
  return `<div style="font-size:12px;line-height:1.4">${rows.join(
    "<br/>"
  )}</div>`;
}

const zoom = defineModel<number>("zoom", { default: 15 });
const center = defineModel<[number, number]>("center");

// Centro interno de l-map: evita que los LatLng de Leaflet se filtren al padre y crasheen el update.
const internalCenter = ref<[number, number]>(
  center.value ?? [4.681414, -74.046864]
);
watch(center, (val) => {
  if (val) internalCenter.value = val;
});

const props = withDefaults(
  defineProps<{
    markers: Array<MarkerData>;
    hoveredId: string | null;
    minZoom?: number;
  }>(),
  { markers: () => [] }
);

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

const mapRef = ref<InstanceType<typeof LMap> | null>(null);
let clusterGroup: any = null;

const specialMarkers = computed(() =>
  props.markers.filter((m) => SPECIAL_TYPES.includes(m.imageType))
);
const poiMarkers = computed(() =>
  props.markers.filter((m) => !SPECIAL_TYPES.includes(m.imageType))
);

function buildCluster() {
  const map = (mapRef.value as any)?.leafletObject as L.Map | undefined;
  if (!map) return;

  if (clusterGroup) map.removeLayer(clusterGroup);

  clusterGroup = new MarkerClusterGroup({
    maxClusterRadius: 50,
    chunkedLoading: true,
  });

  for (const m of poiMarkers.value) {
    const color = POI_COLORS[m.imageType] ?? "#6b7280";
    const icon = L.divIcon({
      html: `<div style="width:10px;height:10px;background:${color};border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4)"></div>`,
      className: "",
      iconSize: [10, 10],
      iconAnchor: [5, 5],
    });
    const marker = L.marker([m.lat, m.lon], { icon }).addTo(clusterGroup);
    if (m.label) marker.bindPopup(buildPoiPopupHtml(m));
  }

  map.addLayer(clusterGroup);
}

function onMapReady() {
  buildCluster();
}

watch(poiMarkers, buildCluster, { deep: true });

onUnmounted(() => {
  const map = (mapRef.value as any)?.leafletObject as L.Map | undefined;
  if (map && clusterGroup) map.removeLayer(clusterGroup);
});

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
