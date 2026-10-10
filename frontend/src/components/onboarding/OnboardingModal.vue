<template>
  <BaseModal :model-value="modelValue" @update:model-value="onToggle">
    <div class="p-4">
      <div class="mb-2 text-center">
        <span
          class="block text-brand-primary text-[10px] sm:text-xs font-semibold sm:font-bold uppercase sm:uppercase tracking-[0.06em] sm:tracking-wider text-center mb-2 sm:mb-1"
        >
          Sabemos que esta decisión no es fácil
        </span>
        <h2
          class="text-sm sm:text-lg leading-snug sm:leading-tight font-semibold sm:font-bold text-brand-text text-center mx-auto max-w-[32ch] sm:max-w-none"
        >
          Cuéntanos qué estás buscando y te mostraremos
          <br class="hidden sm:block" />
          opciones pensadas para ti, sin complicaciones.
        </h2>
      </div>
      <transition name="scale" mode="out-in">
        <IntentSelector
          v-if="step === 'intent'"
          v-model="intent"
          @saved="completeIntent"
        />
        <LocalitySelector v-else-if="step === 'city'" @submit="onCity" />
        <NeighborhoodSelector
          v-else-if="step === 'neighborhood'"
          :saving="saving"
          @submit="onNeighborhoods"
        />
        <PropertyTypeSelector
          v-else-if="step === 'property_type'"
          :saving="saving"
          @submit="onPropertyTypes"
        />
      </transition>
    </div>
    <div class="mb-6 text-center">
      <span
        class="text-xs sm:text-sm text-gray-500 mt-4 text-left sm:text-center max-w-[32ch] sm:max-w-none mx-auto text-muted"
      >
        Puedes cambiar estas opciones más adelante desde Configuración.
      </span>
    </div>
  </BaseModal>
</template>

<script lang="ts" setup>
import { computed, ref } from "vue";
import BaseModal from "@/components/shared/BaseModal.vue";
import IntentSelector from "@/components/onboarding/IntentSelector.vue";
import LocalitySelector from "@/components/onboarding/LocalitySelector.vue";
import NeighborhoodSelector from "@/components/onboarding/NeighborhoodSelector.vue";
import PropertyTypeSelector from "@/components/onboarding/PropertyTypeSelector.vue";
import { useOnboarding } from "@/composables/onboarding/useOnboarding";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import type { CatalogItem } from "@/types/catalog/base";
import type { AccountIntent } from "@/types/users/base";
import type { NeighborhoodSelection } from "@/types/users/interests";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [open: boolean] }>();

const authStore = useAuthStore();
const userStore = useUserStore();
const { completeIntent, saveCity, saveNeighborhoods, savePropertyTypes } =
  useOnboarding();

const step = computed(() => authStore.onboardingStep);
const intent = ref<AccountIntent | null>(null);
const saving = ref(false);

// Cerrar, sea por la X o al terminar, no vuelve a abrirlo en esta sesión.
function close() {
  userStore.dismissModal();
  emit("update:modelValue", false);
}

function onToggle(open: boolean) {
  if (!open) close();
}

async function onCity(localities: CatalogItem[]) {
  saving.value = true;
  await saveCity(localities);
  saving.value = false;
}

async function onNeighborhoods(localities: NeighborhoodSelection[]) {
  saving.value = true;
  await saveNeighborhoods(localities);
  saving.value = false;
}

async function onPropertyTypes(selections: Record<string, string[]>) {
  saving.value = true;
  const saved = await savePropertyTypes(selections);
  saving.value = false;
  if (saved) close();
}
</script>

<style scoped>
.scale-enter-active,
.scale-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
