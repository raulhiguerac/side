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
      <div class="grid grid-cols-4 grid-rows-[200px_200px] gap-[6px] rounded-2xl overflow-hidden">
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
          <span :class="statusStyle" class="px-[10px] py-0.5 rounded-full text-xs font-medium">
            {{ statusLabel }}
          </span>
          <div class="relative group">
            <span :class="verificationStyle" class="px-[10px] py-0.5 rounded-full text-xs font-medium cursor-default">
              {{ verificationLabel }}
            </span>
            <div class="hidden group-hover:block absolute top-[calc(100%+6px)] right-0 w-56 bg-gray-800 text-gray-100 text-[0.7rem] leading-snug p-2 rounded-lg z-10">
              Certificamos que el anuncio cumple nuestras reglas de moderación
              y que la propiedad pertenece al publicante.
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
          <span class="font-medium text-brand-text text-sm">{{ stat.value }}</span>
        </div>
      </div>

      <!-- Description -->
      <div v-if="property.description" class="space-y-2">
        <h2 class="text-base font-semibold text-brand-text">Descripción</h2>
        <p class="text-brand-muted text-sm leading-relaxed">{{ property.description }}</p>
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
            <span class="text-brand-text text-sm font-medium">{{ detail.value }}</span>
          </div>
        </div>
      </div>

      <!-- Bottom: POIs + Map -->
      <div class="flex gap-6 min-h-[320px]">
        <!-- POIs -->
        <div class="w-1/2 space-y-3">
          <h2 class="text-base font-semibold text-brand-text">Cerca del lugar</h2>
          <div class="space-y-1">
            <div
              v-for="poi in mockPois"
              :key="poi.name"
              class="flex items-center gap-3 py-2 border-b border-brand-divider"
            >
              <span class="text-lg">{{ poi.icon }}</span>
              <div>
                <p class="text-sm text-brand-text font-medium">{{ poi.name }}</p>
                <p class="text-xs text-brand-muted">{{ poi.category }} · {{ poi.distance }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Map -->
        <div class="w-1/2 rounded-2xl overflow-hidden">
          <l-map
            v-if="mapCenter"
            :zoom="15"
            :center="mapCenter"
            :options="{ zoomControl: false, scrollWheelZoom: false }"
            style="height: 100%; width: 100%"
          >
            <l-tile-layer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              layer-type="base"
            />
            <l-marker :lat-lng="mapCenter" />
          </l-map>
        </div>
      </div>
    </template>

    <div v-else class="text-brand-muted text-center py-16">
      Propiedad no encontrada.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { LMap, LTileLayer, LMarker } from "@vue-leaflet/vue-leaflet";
import type { PropertyDetail } from "@/types/properties";
import { usePropertyDetail } from "@/composables/properties/usePropertyDetail";

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

const mockPois = [
  { icon: "🏫", name: "Colegio Los Nogales",       category: "Educación",  distance: "350 m"  },
  { icon: "🏥", name: "Clínica del Country",        category: "Salud",      distance: "600 m"  },
  { icon: "🛒", name: "Éxito Chapinero",            category: "Comercio",   distance: "800 m"  },
  { icon: "🌳", name: "Parque El Virrey",           category: "Recreación", distance: "1.1 km" },
  { icon: "🚇", name: "Est. Transmilenio Calle 72", category: "Transporte", distance: "1.4 km" },
];

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
      city_id:         "c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33",
      country_id:      "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
      latitude:  4.709000110626221,
      longitude: -74.02799987792969,
    },
    images: [
      { url: "https://picsum.photos/seed/apt1/800/600", is_cover: true,  display_order: 0 },
      { url: "https://picsum.photos/seed/apt2/400/300", is_cover: false, display_order: 1 },
      { url: "https://picsum.photos/seed/apt3/400/300", is_cover: false, display_order: 2 },
      { url: "https://picsum.photos/seed/apt4/400/300", is_cover: false, display_order: 3 },
      { url: "https://picsum.photos/seed/apt5/400/300", is_cover: false, display_order: 4 },
    ],
  };
  loading.value = false;
});
</script>

<style scoped>
/* grid-area no tiene equivalente limpio en Tailwind arbitrary values con v-for dinámico */
.cell-1 { grid-area: 1 / 1 / 3 / 3; }
.cell-2 { grid-area: 1 / 3 / 2 / 4; }
.cell-3 { grid-area: 1 / 4 / 2 / 5; }
.cell-4 { grid-area: 2 / 3 / 3 / 4; }
.cell-5 { grid-area: 2 / 4 / 3 / 5; }
</style>
