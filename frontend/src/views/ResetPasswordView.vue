<template>
  <!-- Fondo de página -->
  <div
    class="min-h-screen bg-brand-bg flex items-center justify-center p-4 sm:p-8 lg:p-12"
  >
    <div
      class="flex flex-col lg:flex-row w-full max-w-5xl bg-white rounded-2xl lg:rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.08)] overflow-hidden"
    >
      <div
        class="w-full lg:w-1/2 bg-brand-dark flex flex-col items-center justify-center p-8 sm:p-12 lg:p-16"
      >
        <!-- Logo -->
        <div class="flex-1 flex items-center justify-center w-full">
          <img
            src="@/assets/reset-password.svg"
            alt="Logo"
            class="w-3/4 max-w-sm lg:max-w-md h-auto"
          />
        </div>
        <!-- Tagline -->
        <div class="text-left space-y-3">
          <h2
            class="text-center text-white text-base sm:text-lg lg:text-xl font-bold"
          >
            Parece que las llaves se perdieron…
          </h2>
          <p class="text-white/80 text-xs sm:text-sm">
            Te ayudamos a crear una nueva contraseña.
          </p>
        </div>
      </div>
      <div
        class="w-full lg:w-1/2 bg-white p-6 sm:p-10 lg:p-16 flex flex-col items-center justify-center"
      >
        <!-- Header -->
        <div class="flex flex-col items-center gap-4 mb-8">
          <div class="text-center space-y-1">
            <h2 class="text-brand-text text-2xl lg:text-[24px] font-bold">
              ¿Olvidaste la contraseña?
            </h2>
            <p class="text-brand-muted text-sm">
              Tranqui, te ayudamos a recuperar las llaves.
            </p>
            <p class="text-brand-muted text-sm">
              Ingresa el correo con el que te registraste
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
                <input
                  v-model="user.email"
                  type="email"
                  placeholder="correo@ejemplo.com"
                  class="w-full h-12 px-4 bg-white border-[1.5px] border-brand-border rounded-[10px] text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
                />
              </div>
            </div>
            <!-- Botones -->
            <div class="flex flex-col gap-3 mt-6">
              <!-- Botón iniciar sesión -->
              <button
                @click="resetPasswordUser"
                type="submit"
                :disabled="!user.email || isLoading"
                class="w-full h-12 rounded-xl font-semibold transition-all flex items-center justify-center"
                :class="
                  user.email && !isLoading
                    ? 'bg-brand-primary hover:bg-green-600 text-white cursor-pointer'
                    : 'bg-brand-primary-light text-brand-placeholder cursor-not-allowed'
                "
              >
                <svg
                  v-if="isLoading"
                  class="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  />
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                <span v-else>Recupera las llaves</span>
              </button>
            </div>
          </form>
        </div>
        <div class="flex flex-col items-center justify-center py-5">
          <div class="text-center space-y-1">
            <p class="text-brand-muted text-sm">
              Te enviaremos un enlace para crear una nueva contraseña.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/**
 * 🔐 LOGIN VIEW - Pantalla de inicio de sesión
 *
 * Flujo:
 * 1. Usuario llena email y password
 * 2. Llamamos al store.login()
 * 3. Si es exitoso → el store guarda el usuario y redirigimos
 * 4. Si falla → mostramos error
 */
import { ref } from "vue";
import axios from "axios";
import router from "../router";

// 📝 Datos del formulario (locales, no van al store)
const user = ref({
  email: "",
});

const isLoading = ref(false);
const errorMessage = ref(""); // Para mostrar errores al usuario

/**
 * 🔑 Login con email/password
 *
 * Usa el store para hacer el login, así:
 * - El store maneja la cookie automáticamente
 * - El store guarda los datos del usuario
 * - Todos los componentes que usen el store se actualizan
 */
const resetPasswordUser = async () => {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    // 1. Hacemos la petición
    await axios.post(
      "http://localhost:8000/v1/auth/reset-password/request",
      { email: user.value.email }, // Asegúrate de usar .value si es un ref de Vue
      { withCredentials: true }
    );

    // 2. Si llega aquí, es que fue exitoso (status 200)
    // Normalmente el reset no te loguea de inmediato,
    // sino que te avisa que revises tu correo.
    router.push("/login");
  } catch (error: any) {
    // 3. Si algo sale mal (400, 500, etc.)
    errorMessage.value =
      error.response?.data?.message || "Error al solicitar el cambio";
  } finally {
    // 4. Pase lo que pase, quitamos el cargando
    isLoading.value = false;
  }
};
</script>
