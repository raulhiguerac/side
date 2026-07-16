<template>
  <PageContainer class="w-full pb-8">
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
          <PropertyCard
            v-for="card in cards"
            :key="card.id"
            :property="card"
            @click="router.push(`/listing/${card.id}`)"
          />
        </div>

        <div v-else class="text-center text-brand-muted py-20">
          No encontramos propiedades para tus preferencias.
        </div>

        <!-- pagination -->
        <PaginationArrows
          class="mt-10"
          :has-prev="!isFirstPage"
          :has-next="!!nextCursor"
          @prev="loadPrev"
          @next="() => loadNext(nextCursor!)"
        />
      </div>
    </div>
  </PageContainer>
</template>

<script lang="ts" setup>
import { onMounted } from "vue";
import router from "@/router";
import PropertyCard from "@/components/properties/cards/PropertyCard.vue";
import PaginationArrows from "@/components/shared/PaginationArrows.vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import { useFeed } from "@/composables/feed/useFeed";
import { usePropertyMapper } from "@/composables/properties/usePropertyMapper";
import type {
  FeedPreferences,
  FeedFilters as FeedFiltersParams,
} from "@/types/feed";
import FeedFilters from "@/components/properties/feed/FeedFilters.vue";

const { data, loading, load, nextCursor, isFirstPage, loadNext, loadPrev } =
  useFeed();

const { cards } = usePropertyMapper(data);

onMounted(() => load());

async function onSubmit(params: {
  preferences: FeedPreferences;
  filters: FeedFiltersParams;
}) {
  await load(params.preferences, params.filters);
}
</script>
