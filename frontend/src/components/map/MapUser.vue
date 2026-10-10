<template>
  <l-map
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

    <!-- El inmueble que se avalúa: uno solo, fuera del cluster -->
    <l-marker
      v-for="marker in subjectMarkers"
      :key="marker.id"
      :lat-lng="[marker.lat, marker.lon]"
    >
      <l-icon class-name="" :icon-size="[24, 24]" :icon-anchor="[12, 24]">
        <MapPinHouse :size="24" color="white" :fill="BRAND_COLORS.navy" />
      </l-icon>
    </l-marker>

    <slot />
  </l-map>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onUnmounted } from "vue";
import { LIcon, LMarker, LTileLayer, LMap } from "@vue-leaflet/vue-leaflet";
import { MapPinHouse } from "@lucide/vue";
import type * as L from "leaflet";
import type { LeafletEvent } from "leaflet";
import PoiPopup from "@/components/map/PoiPopup.vue";
import { BRAND_COLORS } from "@/constants/brandColors";
import { useMarkerCluster } from "@/composables/map/useMarkerCluster";
import type { BboxPayload } from "@/types/feed/search";
import type { MarkerData } from "@/types/maps/base";
import { renderToElement } from "@/utils/renderToElement";

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
  bbox: [payload: BboxPayload];
  markerClick: [id: string];
  markerHover: [id: string | null];
}>();

const subjectMarkers = computed(() =>
  props.markers.filter((m) => m.imageType === "subject")
);
const clusteredMarkers = computed(() =>
  props.markers.filter((m) => m.imageType !== "subject")
);

const cluster = useMarkerCluster({
  popup: (m) =>
    m.label ? renderToElement(PoiPopup, { marker: m }) : undefined,
  onClick: (m) => emit("markerClick", m.id),
  onHover: (id) => emit("markerHover", id),
});

function onMapReady(instance: L.Map) {
  cluster.attach(instance);
  cluster.sync(clusteredMarkers.value);
  cluster.highlight(props.hoveredId);
}

watch(clusteredMarkers, (markers) => cluster.sync(markers));
watch(
  () => props.hoveredId,
  (id) => cluster.highlight(id)
);

onUnmounted(cluster.detach);

function onMoveEnd(event: LeafletEvent) {
  const map = event.target as L.Map;
  const bounds = map.getBounds();
  emit("bbox", {
    min_lat: bounds.getSouth(),
    max_lat: bounds.getNorth(),
    min_lon: bounds.getWest(),
    max_lon: bounds.getEast(),
    // Del mapa y no del v-model: vue-leaflet lo actualiza con debounce y aquí aún vale el anterior.
    zoom: map.getZoom(),
  });
}
</script>
