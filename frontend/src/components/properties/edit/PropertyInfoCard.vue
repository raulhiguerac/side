<template>
  <div class="bg-white rounded-2xl border border-brand-divider p-6">
    <label
      class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-1"
    >
      Información general
    </label>
    <p class="text-xs text-brand-muted mb-4">
      No se puede modificar luego de publicar.
    </p>
    <div class="flex flex-wrap justify-center gap-3">
      <div
        v-for="chip in infoChips"
        :key="chip.label"
        class="bg-brand-bg rounded-xl px-4 py-4 flex items-center gap-3 w-[calc(50%-0.375rem)] sm:w-[calc(33.333%-0.5rem)]"
      >
        <component :is="chip.icon" class="w-4 h-4 text-brand-muted shrink-0" />
        <div class="min-w-0">
          <div class="text-xs text-brand-muted">{{ chip.label }}</div>
          <div class="text-sm font-semibold text-brand-text truncate">
            {{ chip.value }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import { Home, Building2, Tag, Key, Layers, Calendar, Star } from "@lucide/vue";
import type { PropertyDetail } from "@/types/properties";

const props = defineProps<{
  property: PropertyDetail | null;
}>();

const infoChips = computed(() => {
  const p = props.property;
  if (!p) return [];

  const floorChip =
    p.property_type === "apartment"
      ? { label: "Número de piso", value: p.floor_number ?? "—", icon: Layers }
      : { label: "Total de pisos", value: p.total_floors ?? "—", icon: Layers };

  return [
    {
      label: "Tipo",
      value: p.property_type === "apartment" ? "Apartamento" : "Casa",
      icon: p.property_type === "apartment" ? Building2 : Home,
    },
    {
      label: "Negocio",
      value: p.listing_type === "rent" ? "Arriendo" : "Venta",
      icon: p.listing_type === "rent" ? Key : Tag,
    },
    floorChip,
    {
      label: "Año de construcción",
      value: p.year_built ?? "—",
      icon: Calendar,
    },
    { label: "Estrato", value: p.stratum ?? "—", icon: Star },
  ];
});
</script>
