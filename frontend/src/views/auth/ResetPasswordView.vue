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
          <form
            class="flex flex-col flex-1"
            @submit.prevent="resetPasswordUser"
          >
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
              <BaseButton
                type="submit"
                size="xl"
                :disabled="!user.email"
                :loading="isLoading"
                block
              >
                Recupera las llaves
              </BaseButton>
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
import BaseButton from "@/components/shared/BaseButton.vue";
/** Pantalla de recuperación de contraseña. */
import { ref } from "vue";
import axios from "axios";
import * as usersApi from "@/api/users";
import router from "@/router";

// 📝 Datos del formulario (locales, no van al store)
const user = ref({
  email: "",
});

const isLoading = ref(false);
const errorMessage = ref(""); // Para mostrar errores al usuario

/** Pide el cambio de contraseña y muestra el resultado. */
const resetPasswordUser = async () => {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    // 1. Hacemos la petición
    await usersApi.requestPasswordReset(user.value.email);

    // Éxito: el reset no loguea, solo avisa que revises el correo.
    router.push("/login");
  } catch (error) {
    errorMessage.value =
      (axios.isAxiosError<{ message?: string }>(error) &&
        error.response?.data?.message) ||
      "Error al solicitar el cambio";
  } finally {
    // 4. Pase lo que pase, quitamos el cargando
    isLoading.value = false;
  }
};
</script>
