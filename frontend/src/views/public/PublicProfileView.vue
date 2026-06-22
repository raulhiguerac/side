<template>
  <div class="w-full px-[5%] sm:px-[8%] lg:px-[10%] py-8">
    <!-- Profile header -->
    <div
      class="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-5 bg-white border border-brand-divider rounded-2xl p-5"
    >
      <img
        :src="profile.avatar"
        :alt="profile.name"
        class="w-28 h-28 rounded-full object-cover shrink-0 border border-brand-divider"
      />

      <div class="flex flex-col gap-1.5 flex-1">
        <div class="flex items-center gap-1.5">
          <h1 class="text-brand-text text-lg font-bold">{{ profile.name }}</h1>
          <BadgeCheck class="w-4 h-4 text-brand-primary" />
        </div>
        <span class="text-brand-muted text-xs">{{ profile.role }}</span>

        <div
          class="flex flex-wrap items-center gap-3 text-brand-text text-sm mt-1"
        >
          <span class="flex items-center gap-1">
            <Star class="w-4 h-4 text-yellow-400 fill-yellow-400" />
            {{ profile.rating }}
          </span>
          <span class="text-brand-muted">·</span>
          <span>{{ profile.responseRate }} respuesta</span>
          <span class="text-brand-muted">·</span>
          <span>{{ memberSince }} en la plataforma</span>
          <span class="text-brand-muted">·</span>
          <span>{{ activeListingsCount }} propiedades activas</span>
        </div>
      </div>

      <div class="flex gap-2 shrink-0">
        <button
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-medium hover:bg-green-600 transition"
        >
          <MessageCircle class="w-4 h-4" />
          WhatsApp
        </button>
        <button
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-brand-border text-brand-text text-sm font-medium hover:bg-brand-primary-light transition"
        >
          <MessageSquare class="w-4 h-4" />
          Mensaje
        </button>
        <button
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-brand-border text-brand-text text-sm font-medium hover:bg-brand-primary-light transition"
        >
          <Phone class="w-4 h-4" />
          Llamar
        </button>
      </div>
    </div>

    <div class="border-t border-brand-divider my-8"></div>

    <!-- Listings -->
    <div
      v-if="cards.length"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8"
    >
      <PropertyCard v-for="card in cards" :key="card.id" :property="card" />
    </div>

    <div v-else class="text-center text-brand-muted py-20">
      Este usuario no tiene propiedades publicadas.
    </div>

    <!-- pagination -->
    <div class="flex justify-center items-center gap-4 mt-10">
      <button
        :class="[
          'px-5 py-2 rounded-xl border border-brand-border text-sm font-medium text-brand-text transition hover:bg-brand-primary-light',
          hasPrev ? '' : 'invisible',
        ]"
        @click="prev"
      >
        ← Anterior
      </button>
      <button
        :class="[
          'px-5 py-2 rounded-xl border border-brand-border text-sm font-medium text-brand-text transition hover:bg-brand-primary-light',
          hasNext ? '' : 'invisible',
        ]"
        @click="next"
      >
        Siguiente →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRoute } from "vue-router";
import { BadgeCheck, MessageCircle, MessageSquare, Phone, Star } from "@lucide/vue";
import PropertyCard from "@/components/properties/cards/PropertyCard.vue";
import type { PropertyCardUI } from "@/types/feed";

const route = useRoute();
const userId = route.params.userId as string;

const profile = ref({
  id: "970d29ba-dd16-4d6d-81c6-30e0d9d297b0",
  name: "Mariana Restrepo",
  role: "Agente inmobiliaria",
  avatar: "https://i.pravatar.cc/150?img=47",
  rating: "4.8",
  registeredAt: "2023-02-10",
  responseRate: "95%",
});

const memberSince = computed(() => {
  const registered = new Date(profile.value.registeredAt);
  const months =
    (Date.now() - registered.getTime()) / (1000 * 60 * 60 * 24 * 30);
  const years = Math.floor(months / 12);
  return years >= 1 ? `${years} años` : `${Math.floor(months)} meses`;
});

const allCards = ref<PropertyCardUI[]>([
  {
    id: "1",
    title: "Apartamento en venta",
    price: 320000000,
    location: "Chapinero",
    type: "sale",
    status: "active",
    bedrooms: 3,
    bathrooms: 2,
    area: 85,
  },
  {
    id: "2",
    title: "Apartamento en arriendo",
    price: 1800000,
    location: "Usaquén",
    type: "rent",
    status: "active",
    bedrooms: 2,
    bathrooms: 1,
    area: 60,
  },
  {
    id: "3",
    title: "Casa en venta",
    price: 580000000,
    location: "Suba",
    type: "sale",
    status: "inactive",
    bedrooms: 4,
    bathrooms: 3,
    area: 140,
  },
]);

const activeListingsCount = computed(
  () => allCards.value.filter((c) => c.status === "active").length
);

const PAGE_SIZE = 9;
const page = ref(0);

const hasNext = computed(
  () => (page.value + 1) * PAGE_SIZE < allCards.value.length
);
const hasPrev = computed(() => page.value > 0);

const cards = computed(() =>
  allCards.value.slice(page.value * PAGE_SIZE, (page.value + 1) * PAGE_SIZE)
);

function next() {
  if (hasNext.value) page.value++;
}

function prev() {
  if (hasPrev.value) page.value--;
}
</script>
