<template>
  <!-- Fondo de página -->
  <div
    class="min-h-screen bg-brand-bg flex items-center justify-center p-4 sm:p-8 lg:p-12"
  >
    <!-- <div class="min-h-screen py-40 bg-[#F5F7FA]"> -->
    <!-- <div class="container mx-auto"> -->
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
        <div class="text-center space-y-2">
          <h2 class="text-white text-xl sm:text-2xl lg:text-3xl font-bold">
            Todo empieza aquí
          </h2>
          <p class="text-white/80 text-sm lg:text-base">
            Tu registro toma solo 3 pasos
          </p>
        </div>
      </div>
      <div
        class="w-full lg:w-1/2 bg-white p-6 sm:p-10 lg:p-16 flex flex-col items-center justify-center"
      >
        <!-- Header común para los 3 pasos -->
        <div class="flex flex-col items-center gap-4 mb-8">
          <!-- Título -->
          <div class="text-center space-y-1">
            <h2 class="text-brand-text text-2xl lg:text-[32px] font-bold">
              Regístrate gratis
            </h2>
            <p class="text-brand-muted text-sm">Solo toma 3 pasos</p>
          </div>
          <!-- Step indicator (dots + líneas) -->
          <div class="flex items-center w-64 sm:w-72 px-2">
            <!-- Step 1 -->
            <div class="flex flex-col items-center">
              <div
                class="w-3 h-3 rounded-full"
                :class="step >= 1 ? 'bg-brand-primary' : 'bg-brand-divider'"
              ></div>
              <span
                class="mt-2 text-xs"
                :class="
                  step === 1
                    ? 'text-brand-primary font-semibold'
                    : 'text-brand-placeholder'
                "
                >Perfil</span
              >
            </div>
            <!-- Línea 1-2 -->
            <div
              class="flex-1 h-0.5 mb-6"
              :class="step >= 2 ? 'bg-brand-primary' : 'bg-brand-divider'"
            ></div>

            <!-- Step 2 -->
            <div class="flex flex-col items-center">
              <div
                class="w-3 h-3 rounded-full"
                :class="step >= 2 ? 'bg-brand-primary' : 'bg-brand-divider'"
              ></div>
              <span
                class="mt-2 text-xs"
                :class="
                  step === 2
                    ? 'text-brand-primary font-semibold'
                    : 'text-brand-placeholder'
                "
                >Datos</span
              >
            </div>
            <!-- Línea 2-3 -->
            <div
              class="flex-1 h-0.5 mb-6"
              :class="step >= 3 ? 'bg-brand-primary' : 'bg-brand-divider'"
            ></div>
            <!-- Step 3 -->
            <div class="flex flex-col items-center">
              <div
                class="w-3 h-3 rounded-full"
                :class="step >= 3 ? 'bg-brand-primary' : 'bg-brand-divider'"
              ></div>
              <span
                class="mt-2 text-xs"
                :class="
                  step === 3
                    ? 'text-brand-primary font-semibold'
                    : 'text-brand-placeholder'
                "
                >Seguridad</span
              >
            </div>
          </div>
        </div>
        <div class="w-full h-auto sm:h-[400px] flex flex-col">
          <form class="flex flex-col flex-1">
            <div v-if="step === 1" class="flex flex-col gap-6 flex-1">
              <!-- Paragraph arriba -->
              <p class="text-brand-muted text-sm text-center">
                Cuéntanos cómo quieres usar la plataforma
              </p>
              <!-- Option cards (2, no 3) -->
              <div class="flex flex-col gap-4">
                <button
                  @click="user.accountType = 'person'"
                  class="w-full flex items-center gap-4 p-5 rounded-xl border-2 transition-all"
                  :class="
                    user.accountType === 'person'
                      ? 'bg-brand-primary-light border-brand-primary'
                      : 'bg-white border-brand-border hover:border-brand-muted'
                  "
                >
                  <!-- Icono casa -->
                  <div
                    class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                    :class="
                      user.accountType === 'person'
                        ? 'bg-brand-primary'
                        : 'bg-brand-bg'
                    "
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      :class="
                        user.accountType === 'person'
                          ? 'text-white'
                          : 'text-brand-text'
                      "
                    >
                      <path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" />
                      <path
                        d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
                      />
                    </svg>
                  </div>

                  <!-- Texto -->
                  <div class="flex-1 text-left">
                    <span class="block text-brand-text font-bold"
                      >Persona natural</span
                    >
                    <span class="block text-brand-text text-sm"
                      >Compra, vende o arrienda tu propiedad</span
                    >
                  </div>

                  <!-- Check -->
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="28"
                    height="28"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="flex-shrink-0 transition-opacity"
                    :class="
                      user.accountType === 'person'
                        ? 'text-brand-primary opacity-100'
                        : 'opacity-0'
                    "
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path d="m9 12 2 2 4-4" />
                  </svg>
                </button>
                <button
                  @click="user.accountType = 'organization'"
                  class="w-full flex items-center gap-4 p-5 rounded-xl border-2 transition-all"
                  :class="
                    user.accountType === 'organization'
                      ? 'bg-brand-primary-light border-brand-primary'
                      : 'bg-white border-brand-border hover:border-brand-muted'
                  "
                >
                  <!-- Icono casa -->
                  <div
                    class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                    :class="
                      user.accountType === 'organization'
                        ? 'bg-brand-primary'
                        : 'bg-brand-bg'
                    "
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <rect width="16" height="20" x="4" y="2" rx="2" ry="2" />
                      <path d="M9 22v-4h6v4" />
                      <path d="M8 6h.01" />
                      <path d="M16 6h.01" />
                      <path d="M12 6h.01" />
                      <path d="M12 10h.01" />
                      <path d="M12 14h.01" />
                      <path d="M16 10h.01" />
                      <path d="M16 14h.01" />
                      <path d="M8 10h.01" />
                      <path d="M8 14h.01" />
                    </svg>
                  </div>

                  <!-- Texto -->
                  <div class="flex-1 text-left">
                    <span class="block text-brand-text font-bold"
                      >Inmobiliaria</span
                    >
                    <span class="block text-brand-text text-sm"
                      >Gestiona múltiples propiedades y clientes</span
                    >
                  </div>

                  <!-- Check -->
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="28"
                    height="28"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    class="flex-shrink-0 transition-opacity"
                    :class="
                      user.accountType === 'organization'
                        ? 'text-brand-primary opacity-100'
                        : 'opacity-0'
                    "
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path d="m9 12 2 2 4-4" />
                  </svg>
                </button>
              </div>
              <!-- Botón continuar -->
              <button
                @click="nextStep"
                :disabled="!user.accountType"
                class="w-full h-12 rounded-xl font-semibold transition-all"
                :class="
                  user.accountType
                    ? 'bg-brand-primary hover:bg-green-600 text-white cursor-pointer'
                    : 'bg-brand-primary-light text-brand-placeholder cursor-not-allowed'
                "
              >
                Continuar registro
              </button>
              <!-- Paragraph abajo -->
              <p class="text-brand-placeholder text-xs text-center">
                Sin tarjeta de crédito · Puedes cambiar esto más adelante
              </p>
            </div>
            <div v-if="step === 2" class="flex flex-col flex-1">
              <!-- Texto arriba -->
              <p class="text-brand-muted text-sm text-center mb-6">
                Ahora vamos a conocernos un poco
              </p>

              <!-- Campos -->
              <div class="flex flex-col gap-5">
                <!-- Nombres y Apellidos (fila en desktop, columna en móvil) -->
                <div class="flex flex-col sm:flex-row gap-4">
                  <!-- Nombres -->
                  <div class="flex-1 flex flex-col gap-1.5">
                    <label class="text-brand-text text-xs font-semibold"
                      >Nombres</label
                    >
                    <input
                      v-model="user.name"
                      type="text"
                      placeholder="Nombre completo"
                      class="w-full h-12 px-4 bg-white border-[1.5px] border-brand-border rounded-[10px] text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
                    />
                  </div>

                  <!-- Apellidos -->
                  <div class="flex-1 flex flex-col gap-1.5">
                    <label class="text-brand-text text-xs font-semibold"
                      >Apellidos</label
                    >
                    <input
                      v-model="user.lastName"
                      type="text"
                      placeholder="Apellidos"
                      class="w-full h-12 px-4 bg-white border-[1.5px] border-brand-border rounded-[10px] text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
                    />
                  </div>
                </div>

                <!-- Celular -->
                <div class="flex flex-col gap-1.5">
                  <label class="text-brand-text text-xs font-semibold"
                    >Celular</label
                  >
                  <input
                    v-model="user.phone"
                    type="text"
                    placeholder="Número telefónico +57"
                    class="w-full h-12 px-4 bg-white border-[1.5px] border-brand-border rounded-[10px] text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
                  />
                </div>
              </div>

              <!-- Botones -->
              <div class="flex flex-col gap-3 mt-8">
                <button
                  @click="step--"
                  type="button"
                  class="w-full h-12 rounded-xl font-semibold bg-gray-400 hover:bg-gray-500 text-white transition-all"
                >
                  ← Volver
                </button>
                <button
                  @click="nextStep"
                  :disabled="!user.name || !user.lastName || !user.phone"
                  class="w-full h-12 rounded-xl font-semibold transition-all"
                  :class="
                    user.name && user.lastName && user.phone
                      ? 'bg-brand-primary hover:bg-green-600 text-white cursor-pointer'
                      : 'bg-brand-primary-light text-brand-placeholder cursor-not-allowed'
                  "
                >
                  Siguiente
                </button>
              </div>
            </div>
            <div v-if="step === 3" class="flex flex-col flex-1">
              <!-- Texto arriba -->
              <p class="text-brand-muted text-sm text-center mb-3">
                Todo está listo para mostrarte tu próxima propiedad
              </p>

              <!-- Campos -->
              <div class="flex flex-col gap-2">
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
                        <path
                          d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"
                        />
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

                <!-- Texto protección -->
                <p
                  class="text-brand-placeholder text-xs text-center hidden sm:block"
                >
                  · Tus datos están protegidos
                </p>
                <p
                  class="text-brand-placeholder text-xs text-center hidden sm:block"
                >
                  · Puedes cambiar tu contraseña cuando quieras
                </p>

                <!-- Mensaje de error -->
                <p
                  v-if="errorMessage"
                  class="text-red-500 text-xs text-center bg-red-50 py-2 px-3 rounded-lg"
                >
                  {{ errorMessage }}
                </p>
              </div>

              <!-- Botones -->
              <div class="flex flex-col gap-2 mt-3">
                <button
                  @click="step--"
                  type="button"
                  class="w-full h-10 rounded-xl font-semibold bg-gray-400 hover:bg-gray-500 text-white transition-all text-sm"
                >
                  ← Volver
                </button>
                <!-- Botón finalizar -->
                <button
                  @click="registerUser"
                  :disabled="
                    !user.email ||
                    !user.password ||
                    user.password.length < 8 ||
                    isLoading
                  "
                  class="w-full h-10 rounded-xl font-semibold transition-all text-sm flex items-center justify-center"
                  :class="
                    user.email &&
                    user.password &&
                    user.password.length >= 8 &&
                    !isLoading
                      ? 'bg-brand-primary hover:bg-green-600 text-white cursor-pointer'
                      : 'bg-brand-primary-light text-brand-placeholder cursor-not-allowed'
                  "
                >
                  <BaseSpinner v-if="isLoading" class="h-5 w-5 text-white" />
                  <span v-else>Finalizar registro</span>
                </button>

                <!--
                  Registro con Google, comentado junto con la baja de firebase.
                  Este botón nunca tuvo handler — era decorativo. Vuelve cuando
                  esté el Identity Brokering de Keycloak (ADR-0004).

                  <div class="flex items-center gap-3">
                    <div class="flex-1 h-px bg-brand-divider"></div>
                    <span class="text-brand-muted text-xs"
                      >O registrarse con</span
                    >
                    <div class="flex-1 h-px bg-brand-divider"></div>
                  </div>

                  <button
                    type="button"
                    class="w-full h-10 bg-white border-[1.5px] border-brand-border rounded-[10px] flex items-center justify-center gap-2.5 hover:bg-gray-50 transition-colors"
                  >
                    <img
                      src="https://www.svgrepo.com/show/475656/google-color.svg"
                      class="w-5 h-5"
                      alt="Google"
                    />
                    <span class="text-brand-text text-sm font-medium"
                      >Google</span
                    >
                  </button>
                -->
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/**
 * 📝 REGISTER VIEW - Pantalla de registro (3 pasos)
 *
 * Flujo:
 * 1. Paso 1: Seleccionar tipo de cuenta (persona/organización)
 * 2. Paso 2: Datos personales (nombre, apellido, teléfono)
 * 3. Paso 3: Credenciales (email, password)
 * 4. Al finalizar → llamamos al store.register()
 */
import { ref } from "vue";
import router from "@/router";
import { useAuthStore } from "@/stores/auth";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";

// 🔌 Conectamos con el store de autenticación
const authStore = useAuthStore();

// 📝 Datos del formulario (locales durante el wizard)
const user = ref({
  accountType: "" as "person" | "organization" | "",
  name: "",
  lastName: "",
  phone: "",
  email: "",
  password: "",
});

const step = ref(1);
const showPassword = ref(false);
const isLoading = ref(false);
const errorMessage = ref(""); // Para mostrar errores

// Navegación entre pasos
const nextStep = () => {
  step.value++;
};

/**
 * 📝 Registro con email/password
 *
 * Usa el store para hacer el registro, así:
 * - El store maneja la cookie automáticamente
 * - El store guarda los datos del usuario
 * - Redirigimos al home si es exitoso
 */
const registerUser = async () => {
  isLoading.value = true;
  errorMessage.value = "";

  // Llamamos al store con todos los datos del usuario
  const success = await authStore.register({
    email: user.value.email,
    password: user.value.password,
    first_name: user.value.name,
    last_name: user.value.lastName,
    phone: user.value.phone,
    account_type: user.value.accountType as "person" | "organization",
  });

  if (success) {
    // ✅ Registro exitoso - redirigimos
    router.push("/");
  } else {
    // ❌ Registro fallido
    errorMessage.value =
      "Error al crear la cuenta. El email podría estar en uso.";
  }

  isLoading.value = false;
};
</script>
