<template>
  <!-- Fondo de página -->
  <div
    class="min-h-screen bg-brand-bg flex items-center justify-center p-4 sm:p-8 lg:p-12"
  >
    <div
      class="flex flex-col lg:flex-row w-full max-w-5xl bg-white rounded-2xl lg:rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.08)] overflow-hidden"
    >
      <div
        class="w-full lg:w-1/2 bg-brand-dark flex flex-col items-center justify-center gap-6 p-8 sm:p-12 lg:p-16"
      >
        <!-- Logo -->
        <div class="flex-1 flex items-center justify-center w-full">
          <img
            src="@/assets/logo.svg"
            alt="Logo"
            class="w-3/4 max-w-sm lg:max-w-md h-auto"
          />
        </div>
        <!-- Tagline -->
        <div class="text-left space-y-3">
          <h2
            class="text-center text-white text-base sm:text-lg lg:text-xl font-bold"
          >
            Todo el proceso inmobiliario,
            <span class="block text-brand-accent">en minutos</span>
          </h2>
          <p class="text-white/80 text-xs sm:text-sm">
            Sin trámites innecesarios ni llamadas eternas.
          </p>
          <!-- Bullets -->
          <ul class="text-left space-y-2 pt-2">
            <li
              class="flex items-center gap-2 text-white/90 text-xs sm:text-sm"
            >
              <span class="text-brand-primary">✔</span>
              Publica o encuentra propiedades rápido
            </li>
            <li
              class="flex items-center gap-2 text-white/90 text-xs sm:text-sm"
            >
              <span class="text-brand-primary">✔</span>
              Acompañamiento en cada paso
            </li>
            <li
              class="flex items-center gap-2 text-white/90 text-xs sm:text-sm"
            >
              <span class="text-brand-primary">✔</span>
              Decisiones claras, sin estrés
            </li>
          </ul>
        </div>
      </div>
      <div
        class="w-full lg:w-1/2 bg-white p-6 sm:p-10 lg:p-16 flex flex-col items-center justify-center"
      >
        <!-- Header -->
        <div class="flex flex-col items-center gap-4 mb-8">
          <div class="text-center space-y-1">
            <h2 class="text-brand-text text-2xl lg:text-[32px] font-bold">
              Inicia sesión
            </h2>
            <p class="text-brand-muted text-sm">
              Comprar, vender o arrendar sin vueltas
            </p>
          </div>
        </div>

        <div class="w-full flex flex-col">
          <form class="flex flex-col flex-1" @submit.prevent="loginUser">
            <!-- Campos -->
            <div class="flex flex-col gap-4">
              <!-- Email -->
              <div class="flex flex-col gap-1.5">
                <label class="text-brand-text text-xs font-semibold"
                  >Email</label
                >
                <BaseInput
                  size="lg"
                  v-model="user.email"
                  type="email"
                  placeholder="correo@ejemplo.com"
                />
              </div>

              <!-- Contraseña -->
              <div class="flex flex-col gap-1.5">
                <label class="text-brand-text text-xs font-semibold"
                  >Contraseña</label
                >
                <PasswordInput
                  v-model="user.password"
                  placeholder="••••••••"
                  size="lg"
                />
              </div>

              <!-- Olvidé contraseña -->
              <div class="flex justify-end">
                <router-link
                  to="/forgot-password"
                  class="text-brand-primary text-xs font-medium hover:underline"
                >
                  ¿Olvidaste tu contraseña?
                </router-link>
              </div>

              <!-- Mensaje de error -->
              <p
                v-if="errorMessage"
                class="text-brand-danger text-xs text-center bg-brand-danger-light py-2 px-3 rounded-lg"
              >
                {{ errorMessage }}
              </p>
            </div>

            <!-- Botones -->
            <div class="flex flex-col gap-3 mt-6">
              <!-- Botón iniciar sesión -->
              <BaseButton
                type="submit"
                size="xl"
                :disabled="!user.email || !user.password"
                :loading="isLoading"
                block
              >
                Iniciar sesión
              </BaseButton>

              <!-- Login con Google: vuelve con Keycloak (ADR-0004). -->
            </div>

            <!-- Link a registro -->
            <p class="text-brand-muted text-sm text-center mt-6">
              ¿No tienes cuenta?
              <router-link
                to="/register"
                class="text-brand-primary font-semibold hover:underline"
              >
                Regístrate gratis
              </router-link>
            </p>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import PasswordInput from "@/components/shared/form/PasswordInput.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
import BaseButton from "@/components/shared/BaseButton.vue";
/** Pantalla de login: delega en `store.login()` y redirige, o muestra el error. */
import { ref } from "vue";
import router from "@/router";
import { useAuthStore } from "@/stores/auth";

// 🔌 Conectamos con el store de autenticación
const authStore = useAuthStore();

// 📝 Datos del formulario (locales, no van al store)
const user = ref({
  email: "",
  password: "",
});

const isLoading = ref(false);
const errorMessage = ref(""); // Para mostrar errores al usuario

/** Login vía store: él maneja la cookie, guarda el usuario y propaga el cambio. */
const loginUser = async () => {
  isLoading.value = true;
  errorMessage.value = ""; // Limpiamos errores previos

  // Llamamos al store en vez de axios directamente
  const success = await authStore.login(user.value.email, user.value.password);

  if (success) {
    // ✅ Login exitoso - redirigimos al dashboard o home
    router.push("/");
  } else {
    // ❌ Login fallido - mostramos error
    errorMessage.value = "Email o contraseña incorrectos";
  }

  isLoading.value = false;
};

// El handler de Google se fue con firebase; el botón quedó comentado en el template (ADR-0004).
</script>
