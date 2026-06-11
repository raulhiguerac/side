<template>
  <div class="w-full">
    <div class="px-[5%] sm:px-[8%] lg:px-[10%] pt-8 pb-2">
      <!-- header + toggle -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-brand-text">
            Las escogimos pensando en ti
          </h1>
          <p v-if="isAuthenticated" class="text-sm text-brand-muted mt-1">
            Sin filtros, directo al grano — justo lo que nos contaste que
            buscabas
          </p>
          <p v-else class="text-sm text-brand-muted mt-1">
            Cuéntanos qué buscas y las afinamos para ti
          </p>
        </div>

        <div
          class="inline-flex shrink-0 rounded-xl border border-brand-border bg-white p-1 gap-1"
        >
          <router-link
            :to="{ name: 'feed-list' }"
            class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition"
            :class="
              isList
                ? 'bg-brand-primary text-white'
                : 'text-brand-muted hover:text-brand-text'
            "
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            Lista
          </router-link>
          <router-link
            :to="{ name: 'feed-map' }"
            class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition"
            :class="
              !isList
                ? 'bg-brand-primary text-white'
                : 'text-brand-muted hover:text-brand-text'
            "
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
              />
            </svg>
            Mapa
          </router-link>
        </div>
      </div>
    </div>

    <router-view />
  </div>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const { isAuthenticated } = useAuthStore();
const isList = computed(() => route.name === "feed-list");
</script>
