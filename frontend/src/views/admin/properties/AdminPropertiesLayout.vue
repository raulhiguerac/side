<template>
  <PageContainer>
    <div class="py-8">
      <div class="mb-6">
        <h1 class="text-brand-text text-2xl font-bold flex items-center gap-2">
          <Home class="w-6 h-6 text-brand-primary" />
          Admin — Propiedades
        </h1>
        <p class="text-brand-muted text-sm mt-1">
          Moderación, precios estimados, promociones y carga masiva.
        </p>
      </div>

      <!-- `custom` + `<a>` para leer `isExactActive`; exacto porque `/admin/properties` es prefijo de las otras. -->
      <nav class="flex border-b border-brand-divider">
        <RouterLink
          v-for="tab in TABS"
          :key="tab.to"
          :to="tab.to"
          custom
          v-slot="{ href, navigate, isExactActive }"
        >
          <a
            :href="href"
            @click="navigate"
            class="flex-1 -mb-px border-b-2 pb-3 text-center text-sm font-medium transition-colors"
            :class="
              isExactActive
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-brand-muted hover:text-brand-text'
            "
          >
            {{ tab.label }}
          </a>
        </RouterLink>
      </nav>

      <div class="mt-6">
        <RouterView />
      </div>
    </div>
  </PageContainer>
</template>

<script lang="ts" setup>
import { RouterLink, RouterView } from "vue-router";
import { Home } from "@lucide/vue";
import PageContainer from "@/components/shared/PageContainer.vue";

const TABS = [
  { label: "Moderación", to: "/admin/properties" },
  { label: "Promociones", to: "/admin/properties/promotions" },
  { label: "Importaciones", to: "/admin/properties/imports" },
] as const;
</script>
