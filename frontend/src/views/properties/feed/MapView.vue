<template>
  <PageContainer class="flex h-[80vh] min-h-[360px] gap-4">
    <!-- lista lado izquierdo: scroll infinito sobre todo el bbox -->
    <div
      ref="listRoot"
      class="w-1/2 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
    >
      <div
        v-if="loading && allItems.length === 0"
        class="flex justify-center py-10"
      >
        <BaseSpinner class="h-6 w-6" />
      </div>
      <EmptyState
        v-else-if="allItems.length === 0"
        title="No hay propiedades en esta zona"
        description="Mueve el mapa o aléjate para ver más."
      />
      <div v-else class="grid grid-cols-2 gap-3 py-2">
        <PropertyCard
          v-for="card in cards"
          :key="card.id"
          :property="card"
          :show-favorite="false"
          :class="{ 'ring-2 ring-brand-primary': card.id === mapHoveredId }"
          @click="goToListing(card.id)"
          @mouseenter="hoveredId = card.id"
          @mouseleave="hoveredId = null"
        />
      </div>
      <div ref="sentinel" class="h-px" />
    </div>

    <!-- mapa lado derecho -->
    <div
      class="w-1/2 sticky top-0 self-start h-[80vh] relative rounded-2xl border border-brand-border overflow-hidden"
    >
      <MapUser
        v-model:zoom="zoom"
        v-model:center="center"
        :markers="markers"
        :hovered-id="hoveredId"
        @bbox="onBbox"
        @marker-click="goToListing"
        @marker-hover="mapHoveredId = $event"
      />
    </div>
  </PageContainer>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, watch } from "vue";
import MapUser from "@/components/map/MapUser.vue";
import PropertyCard from "@/components/properties/cards/PropertyCard.vue";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import EmptyState from "@/components/shared/EmptyState.vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import { useFeedMap } from "@/composables/feed/useFeedMap";
import { useInfiniteScroll } from "@/composables/shared/useInfiniteScroll";
import { usePropertyMapper } from "@/composables/properties/usePropertyMapper";
import { useUserStore } from "@/stores/user";
import router from "@/router";
import type { BboxPayload } from "@/types/feed/search";
import type { MarkerData } from "@/types/maps/base";
import { STORAGE_KEYS } from "@/config";

function getInitialCenter(): [number, number] {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.USER_LOCATION);
    if (raw) {
      const loc = JSON.parse(raw);
      if (loc.latitude && loc.longitude) return [loc.latitude, loc.longitude];
    }
  } catch {
    // ignore parse errors, fall through to default
  }
  return [4.681414, -74.046864];
}

const zoom = ref(15);
const center = ref<[number, number]>(getInitialCenter());

const hoveredId = ref<string | null>(null);
const mapHoveredId = ref<string | null>(null);
const listRoot = ref<HTMLElement | null>(null);
const sentinel = ref<HTMLElement | null>(null);

const { allItems, items, loading, fetchByBbox, loadMore } = useFeedMap();
const { cards } = usePropertyMapper(items);
const { recheck } = useInfiniteScroll(sentinel, listRoot, loadMore);

// El mapa pinta todo el bbox; el cluster se encarga de no encimar.
const markers = computed<MarkerData[]>(() =>
  allItems.value.flatMap((p) => {
    const lat = p.location?.latitude;
    const lon = p.location?.longitude;
    if (lat == null || lon == null) return [];
    return [{ id: p.id, lat, lon, imageType: p.property_type }];
  })
);

// Área nueva: la lista vuelve arriba y se re-evalúa si hace falta otra tanda.
watch(allItems, () => {
  if (listRoot.value) listRoot.value.scrollTop = 0;
  recheck();
});

function goToListing(id: string) {
  router.push(`/listing/${id}`);
}

onMounted(async () => {
  const store = useUserStore();
  const loc = await store.detectLocation();
  fetchByBbox({
    min_lat: loc.latitude - 0.05,
    max_lat: loc.latitude + 0.05,
    min_lon: loc.longitude - 0.05,
    max_lon: loc.longitude + 0.05,
    zoom: zoom.value,
  });
});

function onBbox(payload: BboxPayload) {
  router.replace({
    query: {
      min_lat: String(payload.min_lat),
      max_lat: String(payload.max_lat),
      min_lon: String(payload.min_lon),
      max_lon: String(payload.max_lon),
      zoom: String(payload.zoom),
    },
  });
  fetchByBbox(payload);
}
</script>
