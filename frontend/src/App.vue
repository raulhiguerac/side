<template>
  <div class="flex flex-col min-h-screen bg-gray-50">
    <NavBar
      v-if="!$route.meta.hideNavbar"
      :links="navigationLinks"
      class="flex-none shadow-sm z-10"
    />

    <main class="flex flex-col flex-1">
      <router-view v-slot="{ Component }">
        <component :is="Component" class="flex-1" />
      </router-view>
    </main>

    <AppFooter />

    <OnboardingModal v-model="isOnboardingOpen" />
  </div>
</template>

<script lang="ts" setup>
import { watch } from "vue";
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useOnboarding } from "@/composables/onboarding/useOnboarding";
import NavBar from "@/components/shared/NavBar.vue";
import OnboardingModal from "@/components/onboarding/OnboardingModal.vue";
import AppFooter from "@/components/shared/AppFooter.vue";
import { useUserStore } from "./stores/user";
import { ref } from "vue";
import { logger } from "@/utils/logger";

const authStore = useAuthStore();
const userStore = useUserStore();
const { shouldStart } = useOnboarding();
const isOnboardingOpen = ref(false);

const navigationLinks = [
  { names: "Home", router: "/" },
  { names: "About", router: "/about" },
  { names: "Login", router: "/login" },
  { names: "Register", router: "/register" },
];

onMounted(async () => {
  await authStore.checkAuth();
});

watch(
  () => authStore.isAuthenticated,
  async (isLogged) => {
    if (!isLogged) return;
    try {
      await authStore.fillUserData();
      await userStore.checkInterests();
      isOnboardingOpen.value = shouldStart();
    } catch (e) {
      logger.error("Error al inicializar la sesión", e);
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Limpieza de estilos globales */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;

  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}
</style>
