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
      <PropertyPhotoGrid :grid-images="gridImages" :all-images="property.images" />

      <PropertyOverview
        :title="title"
        :location-label="locationLabel"
        :status-label="statusLabel"
        :status-style="statusStyle"
        :verification-label="verificationLabel"
        :verification-style="verificationStyle"
        :formatted-price="formattedPrice"
        :formatted-admin-fee="formattedAdminFee"
        :has-admin-fee="hasAdminFee"
        :description="description"
        :stats="stats"
        :details="details"
      />

      <NearbyPlaces
        v-if="property.location"
        :lat="property.location.latitude"
        :lon="property.location.longitude"
        :property-id="property.id"
      />
    </template>

    <div v-else class="text-brand-muted text-center py-16">
      Propiedad no encontrada.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import type { PropertyDetail } from "@/types/properties";
import { usePropertyDetail } from "@/composables/properties/usePropertyDetail";
import { buildNeighborhoodMap } from "@/composables/catalog/useNeighborhoodLookup";
import propertiesApi from "@/api/propertiesApi";
import PropertyPhotoGrid from "@/components/properties/PropertyPhotoGrid.vue";
import PropertyOverview from "@/components/properties/PropertyOverview.vue";
import NearbyPlaces from "@/components/properties/NearbyPlaces.vue";

const route = useRoute();
const property = ref<PropertyDetail | null>(null);
const loading = ref(true);
const locationLabel = ref<string>("");

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
  gridImages,
  hasAdminFee,
  description,
} = usePropertyDetail(property);

onMounted(async () => {
  const { data } = await propertiesApi.get<PropertyDetail>(
    `/v1/properties/${route.params.id}`
  );
  property.value = data;
  loading.value = false;

  if (property.value.location) {
    const neighborhoodMap = await buildNeighborhoodMap([
      property.value.location.city_id,
    ]);
    locationLabel.value =
      neighborhoodMap[property.value.location.neighborhood_id] ?? "";
  }
});
</script>
