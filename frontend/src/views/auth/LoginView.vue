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
            <span class="block text-[#f3c849]">en minutos</span>
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
                <input
                  v-model="user.email"
                  type="email"
                  placeholder="correo@ejemplo.com"
                  class="w-full h-12 px-4 bg-white border-[1.5px] border-brand-border rounded-[10px] text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
                />
              </div>

              <!-- Contraseña -->
              <div class="flex flex-col gap-1.5">
                <label class="text-brand-text text-xs font-semibold"
                  >Contraseña</label
                >
                <div class="relative">
                  <input
                    v-model="user.password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="••••••••"
                    class="w-full h-12 px-4 pr-12 bg-white border-[1.5px] border-brand-border rounded-[10px] text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
                  />
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="absolute right-4 top-1/2 -translate-y-1/2 text-brand-placeholder hover:text-brand-muted transition-colors"
                  >
                    <!-- Ojo abierto -->
                    <svg
                      v-if="showPassword"
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
                      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                    <!-- Ojo cerrado -->
                    <svg
                      v-else
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
                      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
                      <path
                        d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"
                      />
                      <path
                        d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"
                      />
                      <line x1="2" x2="22" y1="2" y2="22" />
                    </svg>
                  </button>
                </div>
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
                class="text-red-500 text-xs text-center bg-red-50 py-2 px-3 rounded-lg"
              >
                {{ errorMessage }}
              </p>
            </div>

            <!-- Botones -->
            <div class="flex flex-col gap-3 mt-6">
              <!-- Botón iniciar sesión -->
              <button
                type="submit"
                :disabled="!user.email || !user.password || isLoading"
                class="w-full h-12 rounded-xl font-semibold transition-all flex items-center justify-center"
                :class="
                  user.email && user.password && !isLoading
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
                <span v-else>Iniciar sesión</span>
              </button>

              <!-- Divider -->
              <div class="flex items-center gap-3">
                <div class="flex-1 h-px bg-brand-divider"></div>
                <span class="text-brand-muted text-xs">O continuar con</span>
                <div class="flex-1 h-px bg-brand-divider"></div>
              </div>

              <!-- Botón Google -->
              <button
                @click="loginWithGoogle"
                type="button"
                class="w-full h-12 bg-white border-[1.5px] border-brand-border rounded-[10px] flex items-center justify-center gap-2.5 hover:bg-gray-50 transition-colors"
              >
                <img
                  src="https://www.svgrepo.com/show/475656/google-color.svg"
                  class="w-5 h-5"
                  alt="Google"
                />
                <span class="text-brand-text text-sm font-medium">Google</span>
              </button>
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
import router from "@/router";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { useAuthStore } from "@/stores/auth";

// 🔌 Conectamos con el store de autenticación
const authStore = useAuthStore();

// 📝 Datos del formulario (locales, no van al store)
const user = ref({
  email: "",
  password: "",
});

const showPassword = ref(false);
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

/**
 * 🔵 Login con Google
 *
 * Firebase maneja el popup de Google, luego enviamos
 * el token al backend para crear/vincular la cuenta
 */
const loginWithGoogle = async () => {
  try {
    const auth = getAuth();
    const provider = new GoogleAuthProvider();
    const result = await signInWithPopup(auth, provider);
    const idToken = await result.user.getIdToken();

    // El login con Google todavía usa axios porque
    // el flujo es diferente (token de Firebase)
    const response = await axios.post(
      "http://localhost:8000/v1/auth/login/google",
      { token: idToken },
      { withCredentials: true }
    );

    if (response.status === 200) {
      // Después del login con Google, verificamos la sesión
      // para cargar los datos del usuario en el store
      await authStore.checkAuth();
      router.push("/");
    }
  } catch (error) {
    console.error("Error en login con Google:", error);
    errorMessage.value = "Error al iniciar sesión con Google";
  }
};
</script>
