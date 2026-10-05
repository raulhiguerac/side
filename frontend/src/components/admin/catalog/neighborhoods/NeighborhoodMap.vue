<template>
  <div class="h-72 overflow-hidden rounded-xl border border-brand-divider">
    <l-map
      :zoom="FALLBACK_ZOOM"
      :center="initialCenter"
      :options="MAP_OPTIONS"
      @ready="onReady"
    >
      <l-tile-layer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        layer-type="base"
        name="OpenStreetMap"
      />
      <l-geo-json
        v-if="neighbors.length"
        :geojson="neighborsCollection"
        :options-style="NEIGHBOR_STYLE"
        :options="NEIGHBOR_OPTIONS"
      />
      <l-geo-json
        v-if="geometry"
        :geojson="geometry"
        :options-style="SELECTED_STYLE"
      />
    </l-map>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { LGeoJson, LMap, LTileLayer } from "@vue-leaflet/vue-leaflet";
import * as L from "leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import type { Bbox } from "@/composables/admin/useNeighborhoodNeighbors";
import type { NeighborhoodGeometryItem } from "@/types/admin/catalog";

const props = defineProps<{
  geometry: Geometry | null;
  center: [number, number];
  neighbors: NeighborhoodGeometryItem[];
}>();

const emit = defineEmits<{ bounds: [bbox: Bbox] }>();

/** Para un barrio sin geometría: se centra en el centroide con este zoom. */
const FALLBACK_ZOOM = 15;

/** Vista fija: el encuadre lo decide el barrio, no el usuario. */
const MAP_OPTIONS: L.MapOptions = {
  zoomControl: false,
  dragging: false,
  scrollWheelZoom: false,
  doubleClickZoom: false,
  boxZoom: false,
  keyboard: false,
  touchZoom: false,
};

const SELECTED_STYLE = () => ({
  color: "#22C55E",
  weight: 2,
  fillColor: "#22C55E",
  fillOpacity: 0.25,
});

const NEIGHBOR_STYLE = () => ({
  color: "#6B7280",
  weight: 1,
  fillColor: "#9CA3AF",
  fillOpacity: 0.12,
});

const NEIGHBOR_OPTIONS: L.GeoJSONOptions = {
  onEachFeature: (feature, layer) =>
    layer.bindTooltip(feature.properties.name, { sticky: true }),
};

const neighborsCollection = computed<FeatureCollection>(() => ({
  type: "FeatureCollection",
  features: props.neighbors.map(
    (item): Feature => ({
      type: "Feature",
      geometry: item.geometry,
      properties: { id: item.id, name: item.name },
    })
  ),
}));

/** Solo el arranque: después encuadra `frame()`, y atar `center` lo movería en cada render. */
// eslint-disable-next-line vue/no-setup-props-destructure -- sin reactividad a propósito
const initialCenter = props.center;

let map: L.Map | null = null;

function frame() {
  if (!map) return;
  if (props.geometry) {
    map.fitBounds(L.geoJSON(props.geometry).getBounds(), {
      padding: [24, 24],
      animate: false,
    });
  } else {
    map.setView(props.center, FALLBACK_ZOOM, { animate: false });
  }
  const b = map.getBounds();
  emit("bounds", [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()]);
}

function onReady(instance: L.Map) {
  map = instance;
  frame();
}

// Fuentes separadas: un array nuevo con los mismos valores no reencuadra ni repide vecinos.
watch(
  [() => props.geometry, () => props.center[0], () => props.center[1]],
  frame
);
</script>
