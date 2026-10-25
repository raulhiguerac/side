<template>
  <div class="space-y-5">
    <div class="flex flex-col gap-1.5">
      <label for="new-password" class="text-brand-text text-sm font-semibold">
        Nueva contraseña
      </label>
      <PasswordInput
        id="new-password"
        v-model="password"
        autocomplete="new-password"
        placeholder="••••••••"
        size="lg"
      />
      <p class="text-brand-placeholder text-xs">
        Mínimo {{ MIN_PASSWORD_LENGTH }} caracteres
      </p>
    </div>

    <div class="flex flex-col gap-1.5">
      <label
        for="confirm-password"
        class="text-brand-text text-sm font-semibold"
      >
        Confirmar contraseña
      </label>
      <PasswordInput
        id="confirm-password"
        v-model="confirmation"
        autocomplete="new-password"
        placeholder="••••••••"
        size="lg"
        :invalid="mismatch"
      />
      <p v-if="mismatch" class="text-brand-danger text-xs">
        Las contraseñas no coinciden
      </p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from "vue";
import PasswordInput from "@/components/shared/form/PasswordInput.vue";
import { MIN_PASSWORD_LENGTH } from "@/utils/password";

const password = defineModel<string>("password", { default: "" });
const confirmation = defineModel<string>("confirmation", { default: "" });

const mismatch = computed(
  () => !!confirmation.value && password.value !== confirmation.value
);
</script>
