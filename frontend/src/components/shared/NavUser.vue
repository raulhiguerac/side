<template>
  <div class="flex items-center gap-4">
    <!-- Links de navegación para usuario autenticado -->
    <div class="hidden sm:flex items-center gap-6">
      <router-link
        to="/dashboard"
        class="text-white/80 text-sm font-medium hover:text-white transition-colors"
      >
        Dashboard
      </router-link>
      <router-link
        to="/properties"
        class="text-white/80 text-sm font-medium hover:text-white transition-colors"
      >
        Mis propiedades
      </router-link>
    </div>

    <!-- Avatar y dropdown -->
    <div class="relative">
      <button
        @click="isDropdownOpen = !isDropdownOpen"
        class="flex items-center gap-2 p-1 rounded-full hover:bg-white/10 transition-colors"
      >
        <img
          :src="user.avatar || defaultAvatar"
          :alt="user.name"
          class="w-8 h-8 rounded-full object-cover border-2 border-white/20"
        />
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="text-white/60 hidden sm:block"
          :class="{ 'rotate-180': isDropdownOpen }"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      <!-- Dropdown menu -->
      <div
        v-if="isDropdownOpen"
        class="absolute right-0 top-12 w-56 bg-white rounded-xl border border-brand-divider shadow-lg py-2"
      >
        <!-- Info del usuario -->
        <div class="px-4 py-3 border-b border-brand-divider">
          <p class="text-brand-text text-sm font-semibold truncate">
            {{ user.name }}
          </p>
          <p v-if="user.email" class="text-brand-muted text-xs truncate">
            {{ user.email }}
          </p>
        </div>

        <!-- Links del dropdown -->
        <div class="py-2">
          <router-link
            to="/settings/profile"
            @click="isDropdownOpen = false"
            class="flex items-center gap-3 px-4 py-2 text-brand-text text-sm hover:bg-brand-bg transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="8" r="5" />
              <path d="M20 21a8 8 0 0 0-16 0" />
            </svg>
            Mi perfil
          </router-link>
          <router-link
            to="/settings/security"
            @click="isDropdownOpen = false"
            class="flex items-center gap-3 px-4 py-2 text-brand-text text-sm hover:bg-brand-bg transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
              />
              <circle cx="12" cy="12" r="3" />
            </svg>
            Configuración
          </router-link>
        </div>

        <!-- Cerrar sesión -->
        <div class="border-t border-brand-divider pt-2">
          <button
            @click="logout"
            class="flex items-center gap-3 px-4 py-2 w-full text-left text-red-500 text-sm hover:bg-red-50 transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" x2="9" y1="12" y2="12" />
            </svg>
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Overlay para cerrar dropdown al hacer click afuera -->
  <div
    v-if="isDropdownOpen"
    class="fixed inset-0 z-[-1]"
    @click="isDropdownOpen = false"
  ></div>
</template>

<script lang="ts" setup>
import { ref, computed } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const isDropdownOpen = ref(false);

// Datos del usuario desde el store
const user = computed(() => ({
  name: authStore.fullName,
  email: authStore.user?.email || "",
  avatar: authStore.userAvatar,
}));

// Avatar por defecto si no tiene foto
const defaultAvatar =
  "https://ui-avatars.com/api/?name=User&background=22C55E&color=fff";

const logout = async () => {
  isDropdownOpen.value = false;
  await authStore.logout();
};
</script>
