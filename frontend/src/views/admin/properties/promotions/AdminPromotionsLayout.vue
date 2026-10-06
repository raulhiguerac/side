<template>
  <div>
    <AdminTabsNav :tabs="TABS" />

    <div class="mt-6">
      <RouterView />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { RouterView } from "vue-router";
import AdminTabsNav from "@/components/admin/shared/AdminTabsNav.vue";

// Activas y elegibles son dos listados, así que son dos rutas.
const TABS = [
  { label: "Activas", to: "/admin/properties/promotions" },
  { label: "Promocionar", to: "/admin/properties/promotions/new" },
] as const;
</script>
