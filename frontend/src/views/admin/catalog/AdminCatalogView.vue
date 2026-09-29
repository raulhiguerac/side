<template>
  <PageContainer>
    <div class="py-8">
      <div class="mb-6">
        <h1 class="text-brand-text text-2xl font-bold flex items-center gap-2">
          <Globe class="w-6 h-6 text-brand-primary" />
          Admin — Catálogo
        </h1>
        <p class="text-brand-muted text-sm mt-1">
          Países, divisiones, localidades y barrios, con sus geometrías.
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
import { Globe } from "@lucide/vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import AdminTabsNav from "@/components/admin/shared/AdminTabsNav.vue";

const TABS = [
  { label: "Barrios", to: "/admin/catalog" },
  { label: "Localidades", to: "/admin/catalog/localities" },
  { label: "Divisiones", to: "/admin/catalog/admin-divisions" },
  { label: "Países", to: "/admin/catalog/countries" },
] as const;
</script>
