<template>
  <div
    class="flex flex-col min-h-screen xl:h-screen xl:overflow-hidden bg-gray-50"
  >
    <NavBar
      v-if="!$route.meta.hideNavbar"
      :links="navigationLinks"
      class="flex-none shadow-sm z-10"
    />

    <main
      class="flex flex-col flex-1 min-h-0 overflow-y-auto xl:overflow-hidden"
    >
      <router-view v-slot="{ Component }">
        <component :is="Component" class="flex-1" />
      </router-view>
    </main>

    <BaseModal
      v-model="isModalOpen"
      @update:modelValue="(val) => !val && closeFlow()"
    >
      <div class="p-4">
        <div class="mb-6 text-center">
          <span
            class="block text-brand-primary text-[10px] sm:text-xs font-semibold sm:font-bold uppercase sm:uppercase tracking-[0.06em] sm:tracking-wider text-center mb-2 sm:mb-1"
          >
            Sabemos que esta decisión no es fácil
          </span>
          <h2
            class="text-sm sm:text-lg leading-snug sm:leading-tight font-semibold sm:font-bold text-brand-text text-center mx-auto max-w-[32ch] sm:max-w-none"
          >
            Cuéntanos qué estás buscando y te mostraremos
            <br class="hidden sm:block" />
            opciones pensadas para ti, sin complicaciones.
          </h2>
        </div>
        <transition name="scale" mode="out-in">
          <component
            :is="activeComponent"
            v-bind="dynamicProps"
            @complete="closeFlow"
          />
        </transition>
      </div>
      <div class="mb-6 text-center">
        <span
          class="text-xs sm:text-sm text-gray-500 mt-4 text-left sm:text-center max-w-[32ch] sm:max-w-none mx-auto text-muted"
        >
          Puedes cambiar estas opciones más adelante desde Configuración.
        </span>
      </div>
    </BaseModal>
  </div>
</template>

<script lang="ts" setup>
import { watch } from "vue";
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useOnboarding } from "@/composables/useOnboarding";
import NavBar from "@/components/NavBar.vue";
import BaseModal from "@/components/BaseModal.vue";
import { useUserStore } from "./stores/user";
import { ref } from "vue";
import IntentSelector, { type Intent } from "@/components/IntentSelector.vue";
import { computed } from "vue";

const authStore = useAuthStore();
const userStore = useUserStore();
const { activeComponent, isModalOpen, startFlow, closeFlow } = useOnboarding();

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
  (isLogged) => {
    if (!isLogged) return;
    const manualCheck =
      sessionStorage.getItem("onboarding_dismissed") === "true";

    if (!manualCheck) {
      startFlow();
    }
  },
  { immediate: true }
);

const intent = ref<Intent | null>(null);
const dynamicProps = computed(() => {
  if (activeComponent.value === IntentSelector) {
    return {
      modelValue: intent.value,
      "onUpdate:modelValue": (val: Intent) => (intent.value = val),
      onSaved: closeFlow,
    };
  }
  return {};
});
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

.scale-enter-active,
.scale-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.9);
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
