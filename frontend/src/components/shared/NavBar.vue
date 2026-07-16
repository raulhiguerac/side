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
/**
 * 🧭 NAVBAR - Barra de navegación inteligente
 *
 * Esta navbar "sabe" si el usuario está logueado o no,
 * gracias al store de Pinia que actúa como "memoria compartida"
 *
 * Nota: El checkAuth() se hace en App.vue al iniciar la app,
 * así que aquí solo leemos el estado.
 */
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
