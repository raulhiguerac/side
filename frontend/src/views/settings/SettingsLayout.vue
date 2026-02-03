<template>
  <div
    class="bg-brand-bg h-full flex flex-col overflow-auto lg:overflow-hidden"
  >
    <!-- Mobile menu -->
    <div
      class="md:hidden bg-white border-b border-brand-divider sticky top-0 z-10"
    >
      <div class="flex overflow-x-auto px-[5%] py-2 gap-2 no-scrollbar">
        <router-link
          v-for="item in mobileMenu"
          :key="item.path"
          :to="item.path"
          class="flex-shrink-0 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
          :class="
            isActive(item.path)
              ? 'bg-brand-primary text-white'
              : 'bg-brand-bg text-brand-text'
          "
        >
          {{ item.label }}
        </router-link>
      </div>
    </div>

    <!-- Desktop layout -->
    <div
      class="flex items-start px-[5%] sm:px-[8%] lg:px-[10%] flex-1 py-4 md:py-6 lg:overflow-hidden"
    >
      <!-- Sidebar (solo desktop) -->
      <SettingsSidebar class="hidden md:block flex-shrink-0" />

      <!-- Content -->
      <main class="flex-1 md:pl-8 flex flex-col lg:overflow-hidden lg:h-full">
        <router-view class="lg:h-full" />
      </main>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useRoute } from "vue-router";
import SettingsSidebar from "@/components/SettingsSidebar.vue";

const route = useRoute();

const mobileMenu = [
  { path: "/settings/profile", label: "Perfil" },
  { path: "/settings/security", label: "Seguridad" },
  { path: "/settings/account", label: "Cuenta" },
];

const isActive = (path: string) => route.path === path;
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
