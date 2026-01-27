<template>
  <div class="bg-white rounded-xl border border-brand-divider p-4">
    <div class="mb-3">
      <h3 class="text-brand-text text-sm font-semibold">¿Qué buscas?</h3>
    </div>

    <div class="grid grid-cols-2 gap-2">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        @click="selectIntent(option.value)"
        class="flex flex-col items-center gap-1.5 p-3 rounded-lg border transition-all"
        :class="
          modelValue === option.value
            ? 'bg-brand-primary-light border-brand-primary'
            : 'bg-white border-brand-border hover:border-brand-muted'
        "
      >
        <div
          class="w-8 h-8 rounded-lg flex items-center justify-center"
          :class="
            modelValue === option.value ? 'bg-brand-primary' : 'bg-brand-bg'
          "
        >
          <component
            :is="option.icon"
            :class="
              modelValue === option.value ? 'text-white' : 'text-brand-text'
            "
          />
        </div>
        <span
          class="text-xs font-medium"
          :class="
            modelValue === option.value
              ? 'text-brand-primary'
              : 'text-brand-text'
          "
        >
          {{ option.label }}
        </span>
      </button>
    </div>

    <!-- Descripción de la intención seleccionada -->
    <div v-if="selectedDescription" class="mt-3 p-3 bg-brand-bg rounded-lg">
      <p class="text-brand-muted text-xs leading-relaxed">
        {{ selectedDescription }}
      </p>
    </div>

    <!-- Botón guardar -->
    <button
      @click="saveIntent"
      :disabled="isLoading || !hasChanges"
      class="w-full mt-3 py-2 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2"
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
      {{ isLoading ? "Guardando..." : "Guardar" }}
    </button>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, h, watch } from "vue";
import axios from "axios";

export type Intent = "buyer" | "seller" | "renter" | "explorer";

const props = defineProps<{
  modelValue: Intent | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: Intent): void;
  (e: "saved", value: Intent): void;
}>();

const isLoading = ref(false);
const originalValue = ref<Intent | null>(props.modelValue);

// Sync original value when prop changes from parent
watch(
  () => props.modelValue,
  (newVal) => {
    if (originalValue.value === null && newVal !== null) {
      originalValue.value = newVal;
    }
  },
  { immediate: true }
);

const hasChanges = computed(
  () => props.modelValue !== originalValue.value && props.modelValue !== null
);

// Descripciones para cada intención
const descriptions: Record<Intent, string> = {
  buyer:
    "Estás buscando comprar una propiedad. Te mostraremos las mejores opciones de venta disponibles.",
  seller:
    "Quieres vender tu propiedad. Te ayudaremos a publicarla y encontrar compradores.",
  renter: "Buscas arrendar una propiedad o poner la tuya en arriendo.",
  explorer:
    "Solo estás explorando el mercado. Te mostraremos todo tipo de propiedades.",
};

const selectedDescription = computed(() => {
  if (!props.modelValue) return null;
  return descriptions[props.modelValue];
});

// Iconos
const BuyerIcon = () =>
  h(
    "svg",
    {
      xmlns: "http://www.w3.org/2000/svg",
      width: "16",
      height: "16",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
    },
    [
      h("path", { d: "M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" }),
      h("path", {
        d: "M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
      }),
    ]
  );

const SellerIcon = () =>
  h(
    "svg",
    {
      xmlns: "http://www.w3.org/2000/svg",
      width: "16",
      height: "16",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
    },
    [
      h("line", { x1: "12", x2: "12", y1: "2", y2: "22" }),
      h("path", { d: "M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" }),
    ]
  );

const RenterIcon = () =>
  h(
    "svg",
    {
      xmlns: "http://www.w3.org/2000/svg",
      width: "16",
      height: "16",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
    },
    [
      h("rect", {
        width: "18",
        height: "18",
        x: "3",
        y: "4",
        rx: "2",
        ry: "2",
      }),
      h("line", { x1: "16", x2: "16", y1: "2", y2: "6" }),
      h("line", { x1: "8", x2: "8", y1: "2", y2: "6" }),
      h("line", { x1: "3", x2: "21", y1: "10", y2: "10" }),
    ]
  );

const ExplorerIcon = () =>
  h(
    "svg",
    {
      xmlns: "http://www.w3.org/2000/svg",
      width: "16",
      height: "16",
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
    },
    [
      h("circle", { cx: "11", cy: "11", r: "8" }),
      h("path", { d: "m21 21-4.3-4.3" }),
    ]
  );

const options = [
  { value: "buyer" as Intent, label: "Comprar", icon: BuyerIcon },
  { value: "seller" as Intent, label: "Vender", icon: SellerIcon },
  { value: "renter" as Intent, label: "Arrendar", icon: RenterIcon },
  { value: "explorer" as Intent, label: "Explorar", icon: ExplorerIcon },
];

const selectIntent = (value: Intent) => {
  emit("update:modelValue", value);
};

const saveIntent = async () => {
  if (!props.modelValue) return;

  isLoading.value = true;
  try {
    await axios.patch(
      "http://localhost:8000/v1/users/me/profile",
      { intent: props.modelValue },
      { withCredentials: true }
    );
    originalValue.value = props.modelValue;
    emit("saved", props.modelValue);
  } catch (error) {
    console.error("Error al guardar intent:", error);
  } finally {
    isLoading.value = false;
  }
};
</script>
