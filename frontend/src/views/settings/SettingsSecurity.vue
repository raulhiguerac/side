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
    <div class="flex flex-col lg:flex-row gap-4 p-4">
      <div
        class="w-[95%] xl:w-1/2 mx-auto bg-white rounded-2xl border border-brand-divider p-6 md:p-8"
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
            <PasswordInput
              v-model="form.currentPassword"
              placeholder="••••••••"
              size="lg"
            />
          </div>

          <NewPasswordFields
            v-model:password="form.newPassword"
            v-model:confirmation="form.confirmPassword"
          />

          <!-- Error message -->
          <p
            v-if="errorMessage"
            class="text-brand-danger text-sm text-center bg-brand-danger-light py-3 px-4 rounded-xl"
          >
            {{ errorMessage }}
          </p>

          <!-- Success message -->
          <p
            v-if="successMessage"
            class="text-brand-success text-sm text-center bg-brand-success-light py-3 px-4 rounded-xl"
          >
            {{ successMessage }}
          </p>

          <!-- Submit -->
          <BaseButton
            type="submit"
            size="xl"
            :disabled="!canSubmit"
            :loading="isLoading"
            block
          >
            {{ isLoading ? "Actualizando..." : "Actualizar contraseña" }}
          </BaseButton>
        </form>
      </div>
      <!-- Panel derecho - solo en pantallas grandes -->
      <div class="hidden xl:block xl:w-1/2">
        <div
          class="bg-gradient-to-tr from-brand-bg to-brand-primary-light h-full rounded-2xl flex flex-col p-8"
        >
          <div class="flex-1 flex items-center justify-center">
            <img
              src="@/assets/secure-account.svg"
              alt="Logo"
              class="w-1/2 h-auto"
            />
          </div>

          <div class="text-left space-y-3 mt-6">
            <h2
              class="text-center text-brand-muted text-base sm:text-lg lg:text-xl font-bold"
            >
              🔒 Tu seguridad es nuestra prioridad
            </h2>
            <p class="text-brand-muted text-xs sm:text-sm text-center px-4">
              Tu contraseña se guarda de forma segura y nunca la compartimos con
              terceros.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import PasswordInput from "@/components/shared/form/PasswordInput.vue";
import NewPasswordFields from "@/components/shared/form/NewPasswordFields.vue";
import BaseButton from "@/components/shared/BaseButton.vue";
import { ref, computed } from "vue";
import axios from "axios";
import * as usersApi from "@/api/users";
import { isNewPasswordValid } from "@/utils/password";

const isLoading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

const form = ref({
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
});

const canSubmit = computed(
  () =>
    form.value.currentPassword &&
    isNewPasswordValid(form.value.newPassword, form.value.confirmPassword)
);

const changePassword = async () => {
  errorMessage.value = "";
  successMessage.value = "";
  isLoading.value = true;

  try {
    await usersApi.changePassword({
      current_password: form.value.currentPassword,
      new_password: form.value.newPassword,
    });

    successMessage.value = "Contraseña actualizada correctamente";
    form.value = { currentPassword: "", newPassword: "", confirmPassword: "" };
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 400) {
      errorMessage.value = "La contraseña actual es incorrecta";
    } else {
      errorMessage.value = "Error al actualizar la contraseña";
    }
  } finally {
    isLoading.value = false;
  }
};
</script>
