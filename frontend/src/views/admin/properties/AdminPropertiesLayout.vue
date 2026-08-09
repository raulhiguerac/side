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

      <AdminTabsNav :tabs="TABS" stretch />

      <div class="mt-6">
        <RouterView />
      </div>
    </div>
  </PageContainer>
</template>

<script lang="ts" setup>
import { RouterView } from "vue-router";
import { Home } from "@lucide/vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import AdminTabsNav from "@/components/admin/shared/AdminTabsNav.vue";

const TABS = [
  { label: "Moderación", to: "/admin/properties" },
  { label: "Promociones", to: "/admin/properties/promotions" },
  { label: "Importaciones", to: "/admin/properties/imports" },
] as const;
</script>
