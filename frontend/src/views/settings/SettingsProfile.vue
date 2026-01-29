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
        <form @submit.prevent="saveProfile" class="flex flex-col lg:h-full">
          <!-- Avatar centrado -->
          <div class="flex justify-center mb-4 flex-shrink-0">
            <div class="relative">
              <img
                :src="avatarPreview || authStore.userAvatar"
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
                  accept="image/*"
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

          <!-- Actions -->
          <div class="flex justify-end gap-2 flex-shrink-0">
            <button
              type="button"
              @click="resetForm"
              class="px-4 py-1.5 rounded-lg text-sm font-medium text-brand-text border border-brand-border hover:bg-brand-bg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="isLoading || !hasChanges"
              class="px-4 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2"
              :class="
                hasChanges && !isLoading
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
              Guardar
            </button>
          </div>
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
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import IntentSelector, { type Intent } from "@/components/IntentSelector.vue";
import axios from "axios";

const authStore = useAuthStore();
const isLoading = ref(false);
const avatarPreview = ref<string | null>(null);
const avatarFile = ref<File | null>(null);
const intent = ref<Intent | null>(null);

const form = ref({
  first_name: "",
  last_name: "",
  phone: "",
  description: "",
  account_type: "person" as "person" | "organization",
});

const originalForm = ref({ ...form.value });

const hasChanges = computed(() => {
  return (
    JSON.stringify(form.value) !== JSON.stringify(originalForm.value) ||
    avatarFile.value !== null
  );
});

onMounted(() => {
  if (authStore.user) {
    form.value = {
      first_name: authStore.user.first_name || "",
      last_name: authStore.user.last_name || "",
      phone: authStore.user.phone || "",
      description: authStore.user.description || "",
      account_type: authStore.user.account_type || "person",
    };
    originalForm.value = { ...form.value };
    intent.value = (authStore.user.intent as Intent) || null;
  }
});

const handleAvatarChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    const file = input.files[0];
    if (file.size > 2 * 1024 * 1024) {
      alert("La imagen no puede superar 2MB");
      return;
    }
    avatarFile.value = file;
    avatarPreview.value = URL.createObjectURL(file);
  }
};

const resetForm = () => {
  form.value = { ...originalForm.value };
  avatarPreview.value = null;
  avatarFile.value = null;
};

const saveProfile = async () => {
  isLoading.value = true;
  try {
    await axios.patch(
      "http://localhost:8000/v1/users/me/profile",
      {
        first_name: form.value.first_name,
        last_name: form.value.last_name,
        phone: form.value.phone,
        description: form.value.description,
      },
      { withCredentials: true }
    );
    authStore.updateUser(form.value);
    originalForm.value = { ...form.value };
    avatarFile.value = null;
  } catch (error) {
    console.error("Error al guardar perfil:", error);
  } finally {
    isLoading.value = false;
  }
};
</script>
