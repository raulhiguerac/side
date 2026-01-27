<template>
  <div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-brand-text text-2xl font-bold">Seguridad</h1>
      <p class="text-brand-muted text-sm mt-1">
        Gestiona tu contraseña y seguridad
      </p>
    </div>

    <!-- Change Password Card -->
    <div
      class="w-[95%] lg:w-3/5 mx-auto bg-white rounded-2xl border border-brand-divider p-6 md:p-8"
    >
      <div class="flex items-start gap-4 mb-6">
        <div
          class="w-12 h-12 bg-brand-primary-light rounded-xl flex items-center justify-center flex-shrink-0"
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
            class="text-brand-primary"
          >
            <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        </div>
        <div>
          <h3 class="text-brand-text font-semibold">Cambiar contraseña</h3>
          <p class="text-brand-muted text-sm">
            Te recomendamos usar una contraseña segura que no uses en otros
            sitios
          </p>
        </div>
      </div>

      <form @submit.prevent="changePassword" class="space-y-5">
        <!-- Contraseña actual -->
        <div class="flex flex-col gap-1.5">
          <label class="text-brand-text text-sm font-semibold"
            >Contraseña actual</label
          >
          <div class="relative">
            <input
              v-model="form.currentPassword"
              :type="showCurrentPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="w-full h-12 px-4 pr-12 bg-white border-[1.5px] border-brand-border rounded-xl text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
            />
            <button
              type="button"
              @click="showCurrentPassword = !showCurrentPassword"
              class="absolute right-4 top-1/2 -translate-y-1/2 text-brand-placeholder hover:text-brand-muted transition-colors"
            >
              <svg
                v-if="showCurrentPassword"
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
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

        <!-- Nueva contraseña -->
        <div class="flex flex-col gap-1.5">
          <label class="text-brand-text text-sm font-semibold"
            >Nueva contraseña</label
          >
          <div class="relative">
            <input
              v-model="form.newPassword"
              :type="showNewPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="w-full h-12 px-4 pr-12 bg-white border-[1.5px] border-brand-border rounded-xl text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
            />
            <button
              type="button"
              @click="showNewPassword = !showNewPassword"
              class="absolute right-4 top-1/2 -translate-y-1/2 text-brand-placeholder hover:text-brand-muted transition-colors"
            >
              <svg
                v-if="showNewPassword"
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
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
          <p class="text-brand-placeholder text-xs">Mínimo 8 caracteres</p>
        </div>

        <!-- Confirmar contraseña -->
        <div class="flex flex-col gap-1.5">
          <label class="text-brand-text text-sm font-semibold"
            >Confirmar contraseña</label
          >
          <div class="relative">
            <input
              v-model="form.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="w-full h-12 px-4 pr-12 bg-white border-[1.5px] border-brand-border rounded-xl text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary transition-colors"
              :class="{
                'border-red-500': form.confirmPassword && !passwordsMatch,
              }"
            />
            <button
              type="button"
              @click="showConfirmPassword = !showConfirmPassword"
              class="absolute right-4 top-1/2 -translate-y-1/2 text-brand-placeholder hover:text-brand-muted transition-colors"
            >
              <svg
                v-if="showConfirmPassword"
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
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
          <p
            v-if="form.confirmPassword && !passwordsMatch"
            class="text-red-500 text-xs"
          >
            Las contraseñas no coinciden
          </p>
        </div>

        <!-- Error message -->
        <p
          v-if="errorMessage"
          class="text-red-500 text-sm text-center bg-red-50 py-3 px-4 rounded-xl"
        >
          {{ errorMessage }}
        </p>

        <!-- Success message -->
        <p
          v-if="successMessage"
          class="text-green-600 text-sm text-center bg-green-50 py-3 px-4 rounded-xl"
        >
          {{ successMessage }}
        </p>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="!canSubmit || isLoading"
          class="w-full h-12 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2"
          :class="
            canSubmit && !isLoading
              ? 'bg-brand-primary hover:bg-green-600 text-white'
              : 'bg-brand-primary-light text-brand-placeholder cursor-not-allowed'
          "
        >
          <svg
            v-if="isLoading"
            class="animate-spin h-4 w-4"
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
          {{ isLoading ? "Actualizando..." : "Actualizar contraseña" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from "vue";
import axios from "axios";

const isLoading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const showCurrentPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmPassword = ref(false);

const form = ref({
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
});

const passwordsMatch = computed(
  () => form.value.newPassword === form.value.confirmPassword
);

const canSubmit = computed(
  () =>
    form.value.currentPassword &&
    form.value.newPassword.length >= 8 &&
    passwordsMatch.value
);

const changePassword = async () => {
  errorMessage.value = "";
  successMessage.value = "";
  isLoading.value = true;

  try {
    await axios.post(
      "http://localhost:8000/v1/auth/change-password",
      {
        current_password: form.value.currentPassword,
        new_password: form.value.newPassword,
      },
      { withCredentials: true }
    );

    successMessage.value = "Contraseña actualizada correctamente";
    form.value = { currentPassword: "", newPassword: "", confirmPassword: "" };
  } catch (error: any) {
    if (error.response?.status === 400) {
      errorMessage.value = "La contraseña actual es incorrecta";
    } else {
      errorMessage.value = "Error al actualizar la contraseña";
    }
  } finally {
    isLoading.value = false;
  }
};
</script>
