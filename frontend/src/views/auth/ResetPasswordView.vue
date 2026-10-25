<template>
  <AuthLayout>
    <template #aside>
      <div class="flex-1 flex items-center justify-center w-full">
        <img
          src="@/assets/secure-account.svg"
          alt=""
          class="w-3/4 max-w-sm lg:max-w-md h-auto"
        />
      </div>
      <div class="text-left space-y-3">
        <h2
          class="text-center text-white text-base sm:text-lg lg:text-xl font-bold"
        >
          ¡Encontramos las llaves!
        </h2>
        <p class="text-white/80 text-xs sm:text-sm">
          Crea tu nueva contraseña y vuelve a entrar.
        </p>
      </div>
    </template>

    <div class="text-center space-y-1 mb-8">
      <h2 class="text-brand-text text-2xl lg:text-[24px] font-bold">
        Crea una nueva contraseña
      </h2>
      <p class="text-brand-muted text-sm">
        Usa una contraseña que no uses en otros sitios.
      </p>
    </div>

    <div v-if="confirmed" class="w-full flex flex-col items-center gap-4">
      <FormMessage variant="success" class="w-full text-center">
        Listo, tu contraseña se actualizó.
      </FormMessage>
      <router-link
        to="/login"
        class="text-brand-primary text-sm font-medium hover:underline"
      >
        Ir a iniciar sesión
      </router-link>
    </div>

    <div
      v-else-if="invalidLink"
      class="w-full flex flex-col items-center gap-4"
    >
      <FormMessage variant="error" class="w-full text-center">
        {{ error }}
      </FormMessage>
      <router-link
        to="/forgot-password"
        class="text-brand-primary text-sm font-medium hover:underline"
      >
        Pide un enlace nuevo
      </router-link>
    </div>

    <form
      v-else
      class="w-full flex flex-col"
      @submit.prevent="confirmReset(form.newPassword, form.confirmPassword)"
    >
      <NewPasswordFields
        v-model:password="form.newPassword"
        v-model:confirmation="form.confirmPassword"
      />

      <FormMessage v-if="error" variant="error" class="mt-4">
        {{ error }}
      </FormMessage>

      <BaseButton
        type="submit"
        size="xl"
        :disabled="!canSubmit"
        :loading="sending"
        block
        class="mt-6"
      >
        Guardar contraseña
      </BaseButton>
    </form>
  </AuthLayout>
</template>

<script lang="ts" setup>
import { computed, ref } from "vue";
import AuthLayout from "@/components/shared/AuthLayout.vue";
import BaseButton from "@/components/shared/BaseButton.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import NewPasswordFields from "@/components/shared/form/NewPasswordFields.vue";
import { useResetPassword } from "@/composables/users/useResetPassword";
import { isNewPasswordValid } from "@/utils/password";

const form = ref({ newPassword: "", confirmPassword: "" });

const { sending, confirmed, invalidLink, error, confirmReset } =
  useResetPassword();

const canSubmit = computed(() =>
  isNewPasswordValid(form.value.newPassword, form.value.confirmPassword)
);
</script>
