<template>
  <div
    class="w-72 p-6 bg-[#fafafa] border-l border-brand-divider flex flex-col"
  >
    <h3 class="text-brand-text text-sm font-bold mb-4">Resumen</h3>

    <!-- Property type card preview -->
    <div
      v-if="form.property_type"
      class="bg-white border border-brand-divider rounded-2xl p-4 mb-4 flex items-center gap-3"
    >
      <div
        class="w-10 h-10 rounded-xl bg-brand-primary-light flex items-center justify-center"
      >
        <Home
          v-if="form.property_type === 'house'"
          class="w-5 h-5 text-brand-primary"
        />
        <Building2 v-else class="w-5 h-5 text-brand-primary" />
      </div>
      <div>
        <div class="text-sm font-semibold text-brand-text">
          {{ propertyTypeLabel }}
        </div>
        <div class="text-xs text-brand-muted">{{ listingTypeLabel }}</div>
      </div>
    </div>
    <div
      v-else
      class="bg-white border border-dashed border-brand-divider rounded-2xl p-4 mb-4 flex items-center justify-center text-brand-muted text-xs"
    >
      Aún sin selección
    </div>

    <div class="border-t border-brand-divider my-2" />

    <!-- Fields -->
    <div class="flex flex-col gap-3 mt-2">
      <div
        v-for="row in rows"
        :key="row.label"
        class="flex items-center justify-between"
      >
        <div class="flex items-center gap-2 text-xs text-brand-muted">
          <component :is="row.icon" class="w-3.5 h-3.5" />
          {{ row.label }}
        </div>
        <span class="text-xs font-semibold text-brand-text">{{
          row.value ?? "—"
        }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  Home,
  Building2,
  Sparkles,
  Clock,
  Maximize2,
  BedDouble,
  Bath,
  DollarSign,
} from "@lucide/vue";
import type { CreatePropertyForm } from "@/types/properties";

const props = defineProps<{ form: CreatePropertyForm }>();

const propertyTypeLabel = computed(() =>
  props.form.property_type === "house" ? "Casa" : "Apartamento"
);
const listingTypeLabel = computed(() =>
  props.form.listing_type === "sale"
    ? "En venta"
    : props.form.listing_type === "rent"
    ? "En arriendo"
    : "—"
);

const rows = computed(() => [
  {
    label: "Condición",
    icon: props.form.condition === "new" ? Sparkles : Clock,
    value:
      props.form.condition === "new"
        ? "Nueva"
        : props.form.condition === "used"
        ? "Usada"
        : null,
  },
  { label: "Moneda", icon: DollarSign, value: props.form.currency || null },
  {
    label: "Área",
    icon: Maximize2,
    value: props.form.area_m2 ? `${props.form.area_m2} m²` : null,
  },
  {
    label: "Habitaciones",
    icon: BedDouble,
    value: props.form.bedrooms ?? null,
  },
  { label: "Baños", icon: Bath, value: props.form.bathrooms ?? null },
]);
</script>
