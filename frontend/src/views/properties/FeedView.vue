<template>
  <div class="w-full px-[5%] sm:px-[8%] lg:px-[10%] pb-8">
    <div class="flex flex-col lg:flex-row gap-6 items-start">
      <!-- sidebar filters — hidden on mobile, shown on lg+ -->
      <aside
        class="hidden lg:block lg:w-1/4 shrink-0 sticky top-8 bg-white border border-brand-divider rounded-2xl p-5"
      >
        <FeedFilters @submit="onSubmit" />
      </aside>

      <!-- feed cards -->
      <div class="w-full lg:w-3/4">
        <div
          v-if="loading"
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          <div
            v-for="n in 10"
            :key="n"
            class="bg-white rounded-2xl border border-brand-divider h-64 animate-pulse"
          />
        </div>

        <div
          v-else-if="cards.length"
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          <PropertyCard v-for="card in cards" :key="card.id" :property="card" />
        </div>

        <div v-else class="text-center text-brand-muted py-20">
          No encontramos propiedades para tus preferencias.
        </div>

        <!-- pagination -->
        <div class="flex justify-center items-center gap-4 mt-10">
          <button
            :class="[
              'px-5 py-2 rounded-xl border border-brand-border text-sm font-medium text-brand-text transition hover:bg-brand-primary-light',
              isFirstPage ? 'invisible' : '',
            ]"
            @click="loadPrev"
          >
            ← Anterior
          </button>
          <button
            :class="[
              'px-5 py-2 rounded-xl border border-brand-border text-sm font-medium text-brand-text transition hover:bg-brand-primary-light',
              !nextCursor ? 'invisible' : '',
            ]"
            @click="() => loadNext(nextCursor!)"
          >
            Siguiente →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted } from "vue";
import PropertyCard, {
  type Property,
} from "@/components/properties/PropertyCard.vue";
import { useFeed } from "@/composables/feed/useFeed";
import type {
  PropertyCard as FeedCard,
  FeedPreferences,
  FeedFilters as FeedFiltersParams,
} from "@/types/feed";
import FeedFilters from "@/components/properties/FeedFilters.vue";

const {
  data,
  loading,
  load,
  neighborhoodLookup,
  nextCursor,
  isFirstPage,
  loadNext,
  loadPrev,
} = useFeed();

onMounted(() => load());

function toCard(p: FeedCard): Property {
  const typeLabel = p.property_type === "house" ? "Casa" : "Apartamento";
  const listingLabel = p.listing_type === "sale" ? "en venta" : "en arriendo";
  return {
    id: p.id,
    title: `${typeLabel} ${listingLabel}`,
    price: Number(p.price),
    location: neighborhoodLookup.value[p.location?.neighborhood_id ?? ""] ?? "",
    image: p.images.find((i) => i.is_cover)?.url ?? p.images[0]?.url,
    type: p.listing_type,
    bedrooms: p.bedrooms,
    bathrooms: Number(p.bathrooms),
    area: Number(p.area_m2),
  };
}

const cards = computed(() => data.value.map(toCard));

async function onSubmit(params: {
  preferences: FeedPreferences;
  filters: FeedFiltersParams;
}) {
  await load(params.preferences, params.filters);
}
</script>
