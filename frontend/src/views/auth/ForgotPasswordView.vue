<template>
  <AuthLayout>
    <template #aside>
      <div class="flex-1 flex items-center justify-center w-full">
        <img
          src="@/assets/reset-password.svg"
          alt="Logo"
          class="w-3/4 max-w-sm lg:max-w-md h-auto"
        />
      </div>
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
    </template>

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

    <div v-if="sent" class="w-full flex flex-col items-center gap-4">
      <FormMessage variant="success" class="w-full text-center">
        Si el correo está registrado, te llegará un enlace para crear una nueva
        contraseña.
      </FormMessage>
      <p class="text-brand-muted text-xs text-center">
        Ya puedes cerrar esta pestaña o
        <router-link
          to="/login"
          class="text-brand-primary font-medium hover:underline"
        >
          ir a iniciar sesión</router-link
        >.
      </p>
    </div>

    <template v-else>
      <form class="w-full flex flex-col" @submit.prevent="requestReset(email)">
        <div class="flex flex-col gap-1.5">
          <label for="email" class="text-brand-text text-xs font-semibold">
            Email
          </label>
          <BaseInput
            id="email"
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="correo@ejemplo.com"
            size="lg"
          />
        </div>

        <FormMessage v-if="error" variant="error" class="mt-4">
          {{ error }}
        </FormMessage>

        <BaseButton
          type="submit"
          size="xl"
          :disabled="!email"
          :loading="sending"
          block
          class="mt-6"
        >
          Recupera las llaves
        </BaseButton>
      </form>

      <p class="text-brand-muted text-sm text-center py-5">
        Te enviaremos un enlace para crear una nueva contraseña.
      </p>
    </template>
  </AuthLayout>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import AuthLayout from "@/components/shared/AuthLayout.vue";
import BaseButton from "@/components/shared/BaseButton.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
import { useForgotPassword } from "@/composables/users/useForgotPassword";

const email = ref("");

const { sending, sent, error, requestReset } = useForgotPassword();
</script>
