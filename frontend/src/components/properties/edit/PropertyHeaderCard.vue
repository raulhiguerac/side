<template>
  <div class="bg-white rounded-2xl border border-brand-divider p-6">
    <div class="flex items-center justify-between gap-6 flex-wrap">
      <div>
        <div class="flex items-center gap-2 text-brand-text text-lg font-bold">
          <component :is="typeIcon" class="w-5 h-5 text-brand-primary" />
          {{ typeLabel }} en {{ listingLabel }}
          <span
            v-if="property?.status"
            class="px-2 py-0.5 rounded-full text-xs font-semibold"
            :class="LISTING_STATUS_BADGE_CLASSES[property.status]"
          >
            {{ LISTING_STATUS_LABELS[property.status] }}
          </span>
        </div>
        <div class="flex items-center gap-1.5 text-brand-muted text-sm mt-1.5">
          <MapPin class="w-4 h-4" />
          {{ locationLabel || "—" }}
        </div>
      </div>

      <div class="flex gap-7 pl-6 border-l border-brand-divider">
        <div
          v-for="stat in statTiles"
          :key="stat.label"
          class="flex flex-col items-center text-center"
        >
          <component :is="stat.icon" class="w-5 h-5 text-brand-primary" />
          <span class="text-2xl font-bold text-brand-text">{{
            stat.value
          }}</span>
          <span class="text-xs text-brand-muted">{{ stat.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import {
  Home,
  Building2,
  MapPin,
  Maximize2,
  BedDouble,
  Bath,
  Car,
} from "@lucide/vue";
import {
  LISTING_STATUS_LABELS,
  LISTING_STATUS_BADGE_CLASSES,
} from "@/constants/propertyStatus";
import type { PropertyDetail } from "@/types/properties";

const props = defineProps<{
  property: PropertyDetail | null;
  locationLabel: string;
}>();

const typeIcon = computed(() =>
  props.property?.property_type === "apartment" ? Building2 : Home
);
const typeLabel = computed(() =>
  props.property?.property_type === "apartment" ? "Apartamento" : "Casa"
);
const listingLabel = computed(() =>
  props.property?.listing_type === "rent" ? "arriendo" : "venta"
);

const statTiles = computed(() => {
  const p = props.property;
  if (!p) return [];

  return [
    { label: "Área", value: `${Number(p.area_m2)} m²`, icon: Maximize2 },
    { label: "Habitaciones", value: p.bedrooms, icon: BedDouble },
    { label: "Baños", value: Number(p.bathrooms), icon: Bath },
    { label: "Parqueaderos", value: p.parking_spots, icon: Car },
  ];
});
</script>
