<template>
  <AuthLayout
    :illustration="secureAccountIllustration"
    title="Tu casa te sigue esperando"
    subtitle="Reactiva tu cuenta y retoma donde lo dejaste."
  >
    <div class="text-center space-y-1 mb-8">
      <h2 class="text-brand-text text-2xl lg:text-[24px] font-bold">
        Reactiva tu cuenta
      </h2>
      <p v-if="!confirming && !confirmed" class="text-brand-muted text-sm">
        Ingresa el correo con el que te registraste
      </p>
    </div>

    <p v-if="confirming" class="text-brand-muted text-sm text-center">
      Reactivando tu cuenta…
    </p>

    <div v-else-if="confirmed" class="w-full flex flex-col items-center gap-4">
      <FormMessage variant="success" class="w-full text-center">
        Tu cuenta está activa de nuevo. Te llevamos a iniciar sesión…
      </FormMessage>
      <router-link
        :to="{ name: 'login' }"
        class="text-brand-primary text-sm font-medium hover:underline"
      >
        Ir a iniciar sesión
      </router-link>
    </div>

    <div v-else-if="sent" class="w-full flex flex-col items-center gap-4">
      <FormMessage variant="success" class="w-full text-center">
        Si el correo tiene una cuenta desactivada, te llegará un enlace para
        reactivarla.
      </FormMessage>
      <router-link
        :to="{ name: 'login' }"
        class="text-brand-primary text-sm font-medium hover:underline"
      >
        Ir a iniciar sesión
      </router-link>
    </div>

    <template v-else>
      <form
        class="w-full flex flex-col"
        @submit.prevent="requestReactivation(email)"
      >
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

        <FormMessage v-if="invalidLink" variant="error" class="mt-4">
          El enlace no es válido o venció. Pide uno nuevo.
        </FormMessage>
        <FormMessage v-else-if="error" variant="error" class="mt-4">
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
          Reactivar cuenta
        </BaseButton>
      </form>

      <p class="text-brand-muted text-sm text-center py-5">
        Te enviaremos un enlace para reactivar tu cuenta.
      </p>
    </template>
  </AuthLayout>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import secureAccountIllustration from "@/assets/secure-account.svg";
import AuthLayout from "@/components/shared/AuthLayout.vue";
import BaseButton from "@/components/shared/BaseButton.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import BaseInput from "@/components/shared/form/BaseInput.vue";
import { useReactivateAccount } from "@/composables/users/useReactivateAccount";

const email = ref("");

const {
  confirming,
  confirmed,
  invalidLink,
  sending,
  sent,
  error,
  requestReactivation,
} = useReactivateAccount();
</script>
