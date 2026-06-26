<template>
  <div v-show="loading" class="flex items-center justify-center py-20">
    <svg class="animate-spin h-8 w-8 text-brand-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  </div>

  <div v-show="!loading" class="space-y-4">
    <h2 class="text-base font-semibold text-brand-text">Cerca del lugar</h2>

    <!-- Profile buttons -->
    <div class="space-y-1.5">
      <div class="flex flex-col md:flex-row gap-3 md:gap-6">
        <div class="w-full md:w-1/2 flex gap-2 flex-wrap">
          <button
            v-for="p in profiles"
            :key="p.key"
            :class="[
              'flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium border transition-colors',
              activeProfile === p.key
                ? 'bg-brand-primary text-white border-brand-primary'
                : 'bg-white text-brand-muted border-brand-border hover:border-brand-primary hover:text-brand-text',
            ]"
            @click="activeProfile = p.key"
          >
            <component :is="p.icon" :size="16" />
            <span>{{ p.label }}</span>
          </button>
        </div>
        <div class="w-full md:w-1/2 flex justify-center">
          <MapLegend />
        </div>
      </div>
      <p class="text-xs text-brand-muted">
        {{ profiles.find((p) => p.key === activeProfile)?.description }}
      </p>
    </div>

    <!-- POIs + Map -->
    <div class="flex flex-col md:flex-row gap-6">
      <!-- Left: POI accordion by range -->
      <div
        class="order-2 md:order-1 w-full md:w-1/2 h-[500px] overflow-y-auto pr-1 space-y-2"
      >
        <div
          v-for="range in groupedByRange"
          :key="range.minutes"
          class="rounded-xl border border-brand-divider overflow-hidden"
        >
          <!-- Accordion header -->
          <button
            class="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
            @click="
              openRange = openRange === range.minutes ? -1 : range.minutes
            "
          >
            <div class="flex items-center gap-2">
              <span
                :class="range.dot"
                class="inline-block w-2.5 h-2.5 rounded-full"
              />
              <span class="text-sm font-semibold text-brand-text"
                >{{ range.minutes }} min</span
              >
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-brand-muted"
                >{{ range.count }} lugares</span
              >
              <ChevronDown
                :size="14"
                class="text-brand-muted transition-transform"
                :class="openRange === range.minutes ? 'rotate-180' : ''"
              />
            </div>
          </button>

          <!-- Accordion body -->
          <div v-if="openRange === range.minutes" class="px-4 pb-4 pt-1">
            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="group in range.groups.slice(0, 8)"
                :key="group.label"
                class="rounded-xl border border-brand-divider px-3 py-2 space-y-1"
              >
                <div class="flex items-center gap-1.5 text-brand-muted">
                  <component :is="group.icon" :size="13" />
                  <span
                    class="text-[11px] font-medium uppercase tracking-wide"
                    >{{ group.label }}</span
                  >
                </div>
                <p
                  v-for="poi in group.pois"
                  :key="poi.name"
                  class="text-xs text-brand-text truncate"
                >
                  {{ poi.name }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Map -->
      <div
        class="order-1 md:order-2 w-full md:w-1/2 rounded-2xl overflow-hidden"
        style="height: 500px"
      >
        <MapUser
          v-if="mapCenterCoords"
          v-model:zoom="mapZoom"
          v-model:center="mapCenterCoords"
          :markers="poiMarkers"
          :hovered-id="hoveredId"
          :min-zoom="12"
          style="height: 100%; width: 100%"
        >
          <template
            v-for="range in [...groupedByRange].reverse()"
            :key="range.minutes"
          >
            <l-polygon
              v-if="range.isochrone"
              :lat-lngs="range.isochrone.coordinates[0].map((c: number[]) => [c[1], c[0]])"
              :color="ISOCHRONE_COLORS[range.minutes]"
              :fill-color="ISOCHRONE_COLORS[range.minutes]"
              :fill-opacity="0.3"
              :opacity="0"
              :weight="0"
            />
          </template>
        </MapUser>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from "vue";
import { LPolygon } from "@vue-leaflet/vue-leaflet";
import { ChevronDown } from "@lucide/vue";
import type { MarkerData } from "@/types/maps";
import { CATEGORY_META } from "@/types/pois";
import {
  useReachablePois,
  ISOCHRONE_COLORS,
} from "@/composables/pois/useReachablePois";
import MapUser from "@/components/map/MapUser.vue";
import MapLegend from "@/components/map/MapLegend.vue";

const props = defineProps<{
  lat: number;
  lon: number;
  propertyId: string;
}>();

const openRange = ref<number>(5);

const { groupedByRange, loadPois, profiles, activeProfile, loading } =
  useReachablePois("foot-walking");

const hoveredId = ref<string | null>(null);
const mapZoom = ref(14);
const mapCenterCoords = ref<[number, number] | undefined>([
  props.lat,
  props.lon,
]);

const poiMarkers = computed<MarkerData[]>(() => {
  const seen = new Set<string>();
  const markers: MarkerData[] = [];

  if (mapCenterCoords.value) {
    markers.push({
      id: "subject",
      lat: mapCenterCoords.value[0],
      lon: mapCenterCoords.value[1],
      imageType: "subject",
    });
  }

  for (const range of groupedByRange.value) {
    for (const poi of range.pois) {
      const key = `${poi.latitude},${poi.longitude}`;
      if (seen.has(key)) continue;
      seen.add(key);
      markers.push({
        id: key,
        lat: poi.latitude,
        lon: poi.longitude,
        imageType: CATEGORY_META[poi.category ?? ""]?.bucket ?? "poi",
        label: poi.name,
        categoryLabel: CATEGORY_META[poi.category ?? ""]?.label,
        address: poi.full_address ?? undefined,
        phone: poi.phone ?? undefined,
        website: poi.website ?? undefined,
      });
    }
  }
  return markers;
});

watch(loading, async (val) => {
  if (!val) {
    await nextTick();
    window.dispatchEvent(new Event("resize"));
  }
});

onMounted(async () => {
  await loadPois(props.lat, props.lon, props.propertyId);
});
</script>
