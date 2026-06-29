<template>
  <div class="w-full px-[5%] sm:px-[8%] lg:px-[10%] py-8">
    <!-- Profile header -->
    <div
      class="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-5 bg-white border border-brand-divider rounded-2xl p-5"
    >
      <img
        :src="profile?.profile.photo_url ?? undefined"
        :alt="displayName"
        class="w-28 h-28 rounded-full object-cover shrink-0 border border-brand-divider"
      />

      <div class="flex flex-col gap-1.5 flex-1">
        <div class="flex items-center gap-1.5">
          <h1 class="text-brand-text text-lg font-bold">{{ displayName }}</h1>
          <BadgeCheck class="w-4 h-4 text-brand-primary" />
        </div>
        <p v-if="profile?.profile.description" class="text-brand-muted text-sm">
          {{ profile.profile.description }}
        </p>
        <div
          class="flex flex-wrap items-center gap-3 text-brand-text text-sm mt-1"
        >
          <span>{{ memberSince }} en la plataforma</span>
          <span class="text-brand-muted">·</span>
          <span>{{ activeListingsCount }} propiedades activas</span>
        </div>
      </div>

      <div class="flex gap-2 shrink-0">
        <button
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-primary text-white text-sm font-medium hover:bg-green-600 transition"
        >
          <MessageCircle class="w-4 h-4" /> WhatsApp
        </button>
        <button
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-brand-border text-brand-text text-sm font-medium hover:bg-brand-primary-light transition"
        >
          <MessageSquare class="w-4 h-4" /> Mensaje
        </button>
        <button
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-brand-border text-brand-text text-sm font-medium hover:bg-brand-primary-light transition"
        >
          <Phone class="w-4 h-4" /> Llamar
        </button>
      </div>
    </div>

    <div class="border-t border-brand-divider my-8" />

    <!-- Listings -->
    <div
      v-if="cards.length"
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
      Este usuario no tiene propiedades publicadas.
    </div>

    <!-- Pagination -->
    <div class="flex justify-center items-center gap-4 mt-10">
      <button
        :class="[
          'px-5 py-2 rounded-xl border border-brand-border text-sm font-medium text-brand-text transition hover:bg-brand-primary-light',
          { invisible: !hasPrev },
        ]"
        @click="prev"
      >
        ← Anterior
      </button>
      <button
        :class="[
          'px-5 py-2 rounded-xl border border-brand-border text-sm font-medium text-brand-text transition hover:bg-brand-primary-light',
          { invisible: !hasNext },
        ]"
        @click="next"
      >
        Siguiente →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import usersApi from "@/api/usersApi";
import { BadgeCheck, MessageCircle, MessageSquare, Phone } from "@lucide/vue";

import PropertyCard from "@/components/properties/cards/PropertyCard.vue";
import { useProfileListings } from "@/composables/users/useProfileListings";
import { usePropertyMapper } from "@/composables/properties/usePropertyMapper";
import { API } from "@/config";
import type { CurrentUserProfileOut } from "@/types/user";

const route = useRoute();
const router = useRouter();
const userId = route.params.userId as string;

const page = ref(0);
const profile = ref<CurrentUserProfileOut>();

const { listings, hasMore, fetchUserListings, previousListings } =
  useProfileListings();
const { cards } = usePropertyMapper(listings);

onMounted(async () => {
  try {
    const { data } = await usersApi.get<CurrentUserProfileOut>(
      `/v1/users/profiles/${userId}`
    );
    profile.value = data;
  } catch (error) {
    console.error("Error al obtener el perfil:", error);
  }

  await fetchUserListings(userId, page.value * 20);
  page.value++;
});

const displayName = computed(() => {
  const p = profile.value?.profile;
  if (!p) return "";
  return p.account_type === "person"
    ? `${p.first_name} ${p.last_name}`
    : p.display_name;
});

const memberSince = computed(() => {
  const createdAt = profile.value?.profile.created_at;
  if (!createdAt) return "";
  const months =
    (Date.now() - new Date(createdAt).getTime()) / (1000 * 60 * 60 * 24 * 30);
  const years = Math.floor(months / 12);
  return years >= 1 ? `${years} años` : `${Math.floor(months)} meses`;
});

const activeListingsCount = computed(() =>
  hasMore.value ? "+20" : listings.value.length
);
const hasPrev = computed(() => page.value > 1);
const hasNext = computed(() => hasMore.value);

async function next() {
  if (!hasMore.value) return;
  await fetchUserListings(userId, page.value * 20);
  page.value++;
}

function prev() {
  if (!hasPrev.value) return;
  previousListings(page.value);
  page.value--;
}
</script>
