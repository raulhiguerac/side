<template>
  <div class="flex h-[80vh] min-h-[360px] px-[5%] sm:px-[8%] lg:px-[10%] gap-4">
    <!-- lista lado izquierdo -->
    <div class="w-1/2 flex flex-col gap-3 overflow-hidden">
      <div
        class="flex-1 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
      >
        <div class="grid grid-cols-2 gap-3 py-2">
          <PropertyCard
            v-for="card in cards"
            :key="card.id"
            :property="card"
            :show-favorite="false"
            @click="router.push(`/listing/${card.id}`)"
            @mouseenter="hoveredId = card.id"
            @mouseleave="hoveredId = null"
          />
        </div>
      </div>

      <!-- flechas de paginación -->
      <div class="flex items-center justify-center gap-3 pb-2 shrink-0">
        <button
          :disabled="!hasPrev"
          @click="prev"
          class="flex items-center gap-1 px-4 py-2 rounded-xl border border-brand-border text-sm font-medium transition"
          :class="
            hasPrev
              ? 'bg-brand-primary text-white hover:bg-green-600 cursor-pointer'
              : 'opacity-40 cursor-not-allowed'
          "
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Anterior
        </button>
        <button
          :disabled="!hasNext"
          @click="next"
          class="flex items-center gap-1 px-4 py-2 rounded-xl border border-brand-border text-sm font-medium transition"
          :class="
            hasNext
              ? 'bg-brand-primary text-white hover:bg-green-600 cursor-pointer'
              : 'opacity-40 cursor-not-allowed'
          "
        >
          Siguiente
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
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
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from "vue";
import MapUser from "@/components/map/MapUser.vue";
import PropertyCard from "@/components/properties/cards/PropertyCard.vue";
import { useFeedMap } from "@/composables/feed/useFeedMap";
import { usePropertyMapper } from "@/composables/properties/usePropertyMapper";
import { useUserStore } from "@/stores/user";
import router from "@/router";
import type { BboxPayload } from "@/types/feed";
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

const { items, loading, fetchByBbox, next, prev, hasNext, hasPrev } =
  useFeedMap();

const { cards } = usePropertyMapper(items);

const markers = computed(() =>
  items.value
    .filter((p) => p.location?.latitude && p.location?.longitude)
    .map((p) => ({
      id: p.id,
      lat: p.location!.latitude!,
      lon: p.location!.longitude!,
      imageType: p.property_type,
    }))
);

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
