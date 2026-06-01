<template>
  <div class="w-full px-[5%] sm:px-[8%] lg:px-[10%] py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-brand-text">
        Las escogimos pensando en ti
      </h1>
      <p v-if="isAuthenticated" class="text-sm text-brand-muted mt-1">
        Sin filtros, directo al grano — justo lo que nos contaste que buscabas
      </p>
      <p v-else class="text-sm text-brand-muted mt-1">
        Cuéntanos qué buscas y las afinamos para ti
      </p>
    </div>

    <div
      v-if="loading"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8"
    >
      <div
        v-for="n in 10"
        :key="n"
        class="bg-white rounded-2xl border border-brand-divider h-64 animate-pulse"
      />
    </div>

    <div
      v-else-if="cards.length"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8"
    >
      <PropertyCard v-for="card in cards" :key="card.id" :property="card" />
    </div>

    <div v-else class="text-center text-brand-muted py-20">
      No encontramos propiedades para tus preferencias.
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted } from "vue";
import PropertyCard, {
  type Property,
} from "@/components/properties/PropertyCard.vue";
import { useFeed } from "@/composables/feed/useFeed";
import { useAuthStore } from "@/stores/auth";
import type { PropertyCard as FeedCard } from "@/types/feed";

const { isAuthenticated } = useAuthStore();

const { data, loading, load } = useFeed();

onMounted(() => load());

function toCard(p: FeedCard): Property {
  const typeLabel = p.property_type === "house" ? "Casa" : "Apartamento";
  const listingLabel = p.listing_type === "sale" ? "en venta" : "en arriendo";
  return {
    id: p.id,
    title: `${typeLabel} ${listingLabel}`,
    price: Number(p.price),
    location: "",
    image: p.images.find((i) => i.is_cover)?.url ?? p.images[0]?.url,
    type: p.listing_type,
    bedrooms: p.bedrooms,
    bathrooms: Number(p.bathrooms),
    area: Number(p.area_m2),
  };
}

const cards = computed(() => data.value.map(toCard));
</script>
