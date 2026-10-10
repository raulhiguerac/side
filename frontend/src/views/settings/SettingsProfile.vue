<template>
  <div class="lg:h-full flex flex-col">
    <!-- Header -->
    <div class="mb-3 flex-shrink-0">
      <h1 class="text-brand-text text-lg font-bold">Mi Perfil</h1>
      <p class="text-brand-muted text-sm">Actualiza tu información</p>
    </div>

    <!-- Grid: Form + Intent -->
    <div class="flex flex-col lg:flex-row gap-4 flex-1 lg:h-[80%]">
      <!-- Form Card - 50% width on desktop -->
      <div
        class="lg:w-1/2 lg:h-full bg-white rounded-xl border border-brand-divider p-4 flex flex-col"
      >
        <form @submit.prevent="save" class="flex flex-col lg:h-full">
          <fieldset :disabled="saving" class="contents">
            <!-- Avatar centrado -->
            <div class="flex justify-center mb-4 flex-shrink-0">
              <div class="relative">
                <img
                  :src="avatarUrl"
                  alt="Avatar"
                  class="w-20 h-20 rounded-full object-cover border-2 border-brand-bg"
                />
                <label
                  class="absolute bottom-0 right-0 w-7 h-7 bg-brand-primary rounded-full flex items-center justify-center cursor-pointer hover:bg-green-600 shadow-md"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="white"
                    stroke-width="2"
                  >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" x2="12" y1="3" y2="15" />
                  </svg>
                  <input
                    type="file"
                    :accept="LIMITS.PROFILE_PHOTO_TYPES.join(',')"
                    class="hidden"
                    @change="handleAvatarChange"
                  />
                </label>
              </div>
            </div>

            <!-- Nombre y Apellido -->
            <div class="grid grid-cols-2 gap-2 mb-2 flex-shrink-0">
              <input
                v-model="form.first_name"
                type="text"
                placeholder="Nombre"
                class="h-9 px-3 bg-white border border-brand-border rounded-lg text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary"
              />
              <input
                v-model="form.last_name"
                type="text"
                placeholder="Apellido"
                class="h-9 px-3 bg-white border border-brand-border rounded-lg text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary"
              />
            </div>

            <!-- Teléfono -->
            <input
              v-model="form.phone"
              type="tel"
              placeholder="Celular"
              class="h-9 px-3 mb-2 bg-white border border-brand-border rounded-lg text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary flex-shrink-0"
            />

            <!-- Tipo de cuenta -->
            <div
              class="h-9 px-3 mb-2 bg-brand-bg border border-brand-border rounded-lg text-sm text-brand-muted flex items-center flex-shrink-0"
            >
              {{ form.account_type === "person" ? "Persona" : "Inmobiliaria" }}
            </div>

            <!-- Descripción -->
            <textarea
              v-model="form.description"
              placeholder="Descripción"
              class="min-h-[100px] lg:flex-1 lg:min-h-0 px-3 py-2 mb-3 bg-white border border-brand-border rounded-lg text-sm text-brand-text placeholder:text-brand-placeholder focus:outline-none focus:border-brand-primary resize-none"
            ></textarea>

            <FormMessage
              v-if="error"
              variant="error"
              class="mb-3 flex-shrink-0"
            >
              {{ error }}
            </FormMessage>
            <FormMessage
              v-else-if="success"
              variant="success"
              class="mb-3 flex-shrink-0"
            >
              {{ success }}
            </FormMessage>

            <!-- Actions -->
            <div class="flex justify-end gap-2 flex-shrink-0">
              <button
                type="button"
                @click="reset"
                class="px-4 py-1.5 rounded-lg text-sm font-medium text-brand-text border border-brand-border hover:bg-brand-bg"
              >
                Cancelar
              </button>
              <PrimaryButton
                type="submit"
                size="sm"
                :disabled="!hasChanges"
                :loading="saving"
              >
                Guardar
              </PrimaryButton>
            </div>
          </fieldset>
        </form>
      </div>

      <!-- Intent Selector - 50% width -->
      <div class="lg:w-1/2 lg:self-start">
        <IntentSelector v-model="intent" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import IntentSelector from "@/components/onboarding/IntentSelector.vue";
import FormMessage from "@/components/shared/FormMessage.vue";
import PrimaryButton from "@/components/shared/PrimaryButton.vue";
import { useProfileSettings } from "@/composables/users/useProfileSettings";
import { LIMITS } from "@/config";
import type { AccountIntent } from "@/types/users/base";

const authStore = useAuthStore();
const intent = ref<AccountIntent | null>(null);

const {
  form,
  avatarUrl,
  hasChanges,
  saving,
  error,
  success,
  load,
  selectAvatar,
  save,
  reset,
} = useProfileSettings();

onMounted(() => {
  load();
  intent.value = authStore.user?.intent ?? null;
});

function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) selectAvatar(file);
  input.value = "";
}
</script>
