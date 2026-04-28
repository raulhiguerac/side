<template>
  <div class="flex items-center gap-3 sm:gap-6">
    <!-- Links de navegación (desktop) -->
    <div class="hidden sm:flex items-center gap-6">
      <router-link
        to="/"
        class="text-white/80 text-sm font-medium hover:text-white transition-colors"
      >
        Inicio
      </router-link>
      <router-link
        to="/about"
        class="text-white/80 text-sm font-medium hover:text-white transition-colors"
      >
        Conócenos
      </router-link>
      <router-link
        to="/login"
        class="text-white/80 text-sm font-medium hover:text-white transition-colors"
      >
        Iniciar sesión
      </router-link>
    </div>

    <!-- Botón Registrarse (siempre visible) -->
    <router-link
      to="/register"
      class="bg-brand-primary hover:bg-green-600 text-white text-xs sm:text-sm font-semibold px-3 sm:px-5 py-1.5 sm:py-2 rounded-lg transition-all"
    >
      Registrarse
    </router-link>

    <!-- Menú móvil -->
    <div class="sm:hidden relative">
      <button
        @click="isMenuOpen = !isMenuOpen"
        class="text-white/80 hover:text-white transition-colors p-1"
      >
        <!-- Icono hamburguesa / X -->
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <template v-if="!isMenuOpen">
            <line x1="4" x2="20" y1="12" y2="12" />
            <line x1="4" x2="20" y1="6" y2="6" />
            <line x1="4" x2="20" y1="18" y2="18" />
          </template>
          <template v-else>
            <line x1="18" x2="6" y1="6" y2="18" />
            <line x1="6" x2="18" y1="6" y2="18" />
          </template>
        </svg>
      </button>

      <!-- Dropdown -->
      <div
        v-if="isMenuOpen"
        class="absolute right-0 top-full mt-2 w-48 bg-brand-dark border border-white/10 rounded-lg shadow-lg py-2"
      >
        <router-link
          to="/"
          @click="isMenuOpen = false"
          class="block px-4 py-2 text-white/80 text-sm hover:text-white hover:bg-white/5 transition-colors"
        >
          Inicio
        </router-link>
        <router-link
          to="/about"
          @click="isMenuOpen = false"
          class="block px-4 py-2 text-white/80 text-sm hover:text-white hover:bg-white/5 transition-colors"
        >
          Conócenos
        </router-link>
        <router-link
          to="/login"
          @click="isMenuOpen = false"
          class="block px-4 py-2 text-white/80 text-sm hover:text-white hover:bg-white/5 transition-colors"
        >
          Iniciar sesión
        </router-link>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";

const isMenuOpen = ref(false);
</script>
