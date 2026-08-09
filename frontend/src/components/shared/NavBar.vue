<template>
  <nav class="bg-brand-dark w-full relative z-50">
    <PageContainer class="flex items-center justify-between py-1">
      <!-- Logo -->
      <router-link to="/" class="flex items-center">
        <img src="@/assets/logo.svg" alt="Logo" class="h-8 sm:h-10" />
      </router-link>

      <!-- Componente condicional según autenticación -->
      <NavGuest v-if="!isAuthenticated" />
      <NavUser v-else />
    </PageContainer>
  </nav>
</template>

<script lang="ts" setup>
/** Solo lee el estado de auth del store; el `checkAuth()` lo hace App.vue al iniciar. */
import { computed } from "vue";
import NavGuest from "./NavGuest.vue";
import NavUser from "./NavUser.vue";
import PageContainer from "./PageContainer.vue";
import { useAuthStore } from "@/stores/auth";

// 🔌 Conectamos con el store
const authStore = useAuthStore();

// 📊 Solo necesitamos saber si está autenticado
const isAuthenticated = computed(() => authStore.isAuthenticated);
</script>
