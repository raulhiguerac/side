<template>
  <div class="w-full px-[8%] sm:px-[12%] lg:px-[18%] py-8 space-y-6">
    <!-- Loading skeleton -->
    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-[400px] bg-brand-divider rounded-2xl" />
      <div class="h-8 bg-brand-divider rounded w-1/3" />
      <div class="h-4 bg-brand-divider rounded w-1/4" />
    </div>

    <template v-else-if="property">
      <!-- Photo grid -->
      <div
        class="grid grid-cols-4 grid-rows-[200px_200px] gap-[6px] rounded-2xl overflow-hidden"
      >
        <div
          v-for="(img, i) in gridImages"
          :key="i"
          :class="`cell-${i + 1}`"
          class="overflow-hidden group cursor-pointer"
        >
          <img
            :src="img.url"
            :alt="`Foto ${i + 1}`"
            class="w-full h-full object-cover transition-transform duration-200 group-hover:scale-[1.03]"
          />
        </div>
      </div>

      <!-- Header: title + badges -->
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold text-brand-text">{{ title }}</h1>
          <p class="text-sm text-brand-muted mt-0.5">Bosque Medina, Bogotá</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span
            :class="statusStyle"
            class="px-[10px] py-0.5 rounded-full text-xs font-medium"
          >
            {{ statusLabel }}
          </span>
          <div class="relative group">
            <span
              :class="verificationStyle"
              class="px-[10px] py-0.5 rounded-full text-xs font-medium cursor-default"
            >
              {{ verificationLabel }}
            </span>
            <div
              class="hidden group-hover:block absolute top-[calc(100%+6px)] right-0 w-56 bg-gray-800 text-gray-100 text-[0.7rem] leading-snug p-2 rounded-lg z-10"
            >
              Certificamos que el anuncio cumple nuestras reglas de moderación y
              que la propiedad pertenece al publicante.
            </div>
          </div>
        </div>
      </div>

      <!-- Price -->
      <div class="space-y-1">
        <p class="text-3xl font-bold text-brand-text">{{ formattedPrice }}</p>
        <p v-if="property.admin_fee" class="text-sm text-brand-muted">
          Admin: {{ formattedAdminFee }}
        </p>
      </div>

      <!-- Stats chips -->
      <div class="grid grid-cols-3 sm:grid-cols-6 gap-3">
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="flex flex-col items-center gap-0.5 px-4 py-2 border border-brand-divider rounded-xl"
        >
          <span class="text-brand-muted text-xs">{{ stat.label }}</span>
          <span class="font-medium text-brand-text text-sm">{{
            stat.value
          }}</span>
        </div>
      </div>

      <!-- Description -->
      <div v-if="property.description" class="space-y-2">
        <h2 class="text-base font-semibold text-brand-text">Descripción</h2>
        <p class="text-brand-muted text-sm leading-relaxed">
          {{ property.description }}
        </p>
      </div>

      <!-- Secondary details -->
      <div class="space-y-2">
        <h2 class="text-base font-semibold text-brand-text">Detalles</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div
            v-for="detail in details"
            :key="detail.label"
            class="flex flex-col gap-0.5 px-3 py-2 bg-gray-50 rounded-[10px]"
          >
            <span class="text-brand-muted text-xs">{{ detail.label }}</span>
            <span class="text-brand-text text-sm font-medium">{{
              detail.value
            }}</span>
          </div>
        </div>
      </div>

      <!-- Cerca del lugar -->
      <div class="space-y-4">
        <h2 class="text-base font-semibold text-brand-text">Cerca del lugar</h2>

        <!-- Profile buttons -->
        <div class="space-y-1.5">
          <div class="flex gap-2">
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
          <p class="text-xs text-brand-muted">
            {{ profiles.find((p) => p.key === activeProfile)?.description }}
          </p>
        </div>

        <!-- POIs + Map -->
        <div class="flex gap-6 min-h-[500px]">
          <!-- Left: POI accordion by range -->
          <div class="w-1/2 h-[500px] overflow-y-auto pr-1 space-y-2">
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
          <div class="w-1/2 rounded-2xl overflow-hidden" style="height: 500px">
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

    <div v-else class="text-brand-muted text-center py-16">
      Propiedad no encontrada.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { LPolygon } from "@vue-leaflet/vue-leaflet";
import { ChevronDown } from "@lucide/vue";
import type { PropertyDetail } from "@/types/properties";
import type { MarkerData, MarkerImageType } from "@/types/maps";
import { usePropertyDetail } from "@/composables/properties/usePropertyDetail";
import {
  useReachablePois,
  ISOCHRONE_COLORS,
} from "@/composables/pois/useReachablePois";
import MapUser from "@/components/map/MapUser.vue";

const CATEGORY_TO_MARKER: Record<string, MarkerImageType> = {
  school: "education",
  kindergarten: "education",
  college: "education",
  university: "education",
  hospital: "health",
  clinic: "health",
  doctor: "health",
  dentist: "health",
  pharmacy: "health",
  restaurant: "food",
  cafe: "food",
  fast_food: "food",
  bakery: "food",
  supermarket: "commerce",
  convenience: "commerce",
  bus_station: "transport",
  platform: "transport",
  stop_position: "transport",
};

const openRange = ref<number>(5);
const property = ref<PropertyDetail | null>(null);
const loading = ref(true);

const {
  title,
  formattedPrice,
  formattedAdminFee,
  stats,
  details,
  statusLabel,
  statusStyle,
  verificationLabel,
  verificationStyle,
  mapCenter,
  gridImages,
} = usePropertyDetail(property);

const {
  ranges,
  groupedByRange,
  loading: poisLoading,
  loadPois,
  profiles,
  activeProfile,
} = useReachablePois("foot-walking");

const hoveredId = ref<string | null>(null);
const mapZoom = ref(14);
const mapCenterCoords = ref<[number, number] | undefined>();

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
        imageType: CATEGORY_TO_MARKER[poi.category ?? ""] ?? "poi",
      });
    }
  }
  return markers;
});

onMounted(async () => {
  // TODO: centralizar fetch en composable/api layer
  // const { data } = await axios.get(`/api/v1/properties/${route.params.id}`);
  property.value = {
    id: "063c3edc-eadc-4b9a-a4b8-afd84cc8c604",
    property_type: "apartment",
    listing_type: "sale",
    condition: "used",
    status: "active",
    verification_status: "unverified",
    price: 2380000000,
    currency: "COP",
    admin_fee: 1657000,
    area_m2: 339,
    bedrooms: 4,
    bathrooms: 4,
    parking_spots: 4,
    floor_number: 0,
    total_floors: null,
    stratum: 6,
    description:
      "Buscas apartamento amplio, con buenos espacios y vista hacia los cerros orientales. Esta puede ser tu gran oportunidad: apartamento ubicado al costado sur de Bosque Medina con tres balcones y cuatro terrazas, en conjunto con club house con Gimnasio, Jaula de Golf, Piscina, turco, BBQ, Cancha de squash y teatrino.",
    year_built: null,
    created_at: "2026-05-31T19:40:49.583640+00:00",
    location: {
      neighborhood_id: "c9db96cc-3879-4303-9d3a-d50e2c4bfaac",
      city_id: "c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33",
      country_id: "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
      latitude: 4.709000110626221,
      longitude: -74.02799987792969,
    },
    images: [
      {
        url: "https://picsum.photos/seed/apt1/800/600",
        is_cover: true,
        display_order: 0,
      },
      {
        url: "https://picsum.photos/seed/apt2/400/300",
        is_cover: false,
        display_order: 1,
      },
      {
        url: "https://picsum.photos/seed/apt3/400/300",
        is_cover: false,
        display_order: 2,
      },
      {
        url: "https://picsum.photos/seed/apt4/400/300",
        is_cover: false,
        display_order: 3,
      },
      {
        url: "https://picsum.photos/seed/apt5/400/300",
        is_cover: false,
        display_order: 4,
      },
    ],
  };
  loading.value = false;

  if (property.value?.location) {
    mapCenterCoords.value = [
      property.value.location.latitude,
      property.value.location.longitude,
    ];
    await loadPois(
      property.value.location.latitude,
      property.value.location.longitude,
      property.value.id
    );
  }
});
</script>

<style scoped>
/* grid-area no tiene equivalente limpio en Tailwind arbitrary values con v-for dinámico */
.cell-1 {
  grid-area: 1 / 1 / 3 / 3;
}
.cell-2 {
  grid-area: 1 / 3 / 2 / 4;
}
.cell-3 {
  grid-area: 1 / 4 / 2 / 5;
}
.cell-4 {
  grid-area: 2 / 3 / 3 / 4;
}
.cell-5 {
  grid-area: 2 / 4 / 3 / 5;
}
</style>
