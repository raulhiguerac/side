<template>
  <div class="flex flex-col flex-1 gap-6">
    <!-- Step indicator -->
    <div class="flex items-center">
      <template v-for="(label, i) in stepLabels" :key="i">
        <div class="flex flex-col items-center">
          <div
            class="w-3 h-3 rounded-full transition-colors duration-300"
            :class="step >= i + 1 ? 'bg-brand-primary' : 'bg-brand-divider'"
          />
          <span
            class="mt-1.5 text-xs transition-colors duration-300"
            :class="
              step === i + 1
                ? 'text-brand-primary font-semibold'
                : 'text-brand-placeholder'
            "
            >{{ label }}</span
          >
        </div>
        <div
          v-if="i < stepLabels.length - 1"
          class="flex-1 h-0.5 mb-5 transition-colors duration-300"
          :class="step >= i + 2 ? 'bg-brand-primary' : 'bg-brand-divider'"
        />
      </template>
    </div>

    <!-- Step content -->
    <div class="flex flex-col flex-1">
      <Transition name="step" mode="out-in">
        <!-- STEP 1: Tipo -->
        <div v-if="step === 1" key="s1" class="flex flex-col flex-1">
          <div>
            <h2 class="text-brand-text text-xl font-bold">
              ¿Qué tipo de inmueble es?
            </h2>
            <p class="text-brand-muted text-sm mt-1">
              Selecciona el tipo de propiedad a avaluar.
            </p>
          </div>
          <div class="flex flex-col gap-6 my-auto py-6">
            <button
              @click="form.property_type = 'apartment'"
              class="w-full flex items-center justify-center gap-4 px-6 py-7 rounded-2xl border-2 transition-all duration-200"
              :class="
                form.property_type === 'apartment'
                  ? 'border-brand-primary bg-brand-primary-light'
                  : 'border-brand-divider hover:border-brand-border'
              "
            >
              <svg
                class="w-6 h-6 flex-shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                :class="
                  form.property_type === 'apartment'
                    ? 'text-brand-primary'
                    : 'text-brand-muted'
                "
              >
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="M9 21V9h6v12" />
                <path d="M3 9h18" />
                <path d="M9 13h1m5 0h-1M9 16h1m5 0h-1" />
              </svg>
              <span
                class="font-semibold text-sm"
                :class="
                  form.property_type === 'apartment'
                    ? 'text-brand-primary'
                    : 'text-brand-text'
                "
                >Apartamento</span
              >
            </button>
            <button
              @click="form.property_type = 'house'"
              class="w-full flex items-center justify-center gap-4 px-6 py-7 rounded-2xl border-2 transition-all duration-200"
              :class="
                form.property_type === 'house'
                  ? 'border-brand-primary bg-brand-primary-light'
                  : 'border-brand-divider hover:border-brand-border'
              "
            >
              <svg
                class="w-6 h-6 flex-shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                :class="
                  form.property_type === 'house'
                    ? 'text-brand-primary'
                    : 'text-brand-muted'
                "
              >
                <path d="M3 12L12 3l9 9" />
                <path d="M5 10v10a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1V10" />
              </svg>
              <span
                class="font-semibold text-sm"
                :class="
                  form.property_type === 'house'
                    ? 'text-brand-primary'
                    : 'text-brand-text'
                "
                >Casa</span
              >
            </button>
          </div>
        </div>

        <!-- STEP 2: Detalles -->
        <div
          v-else-if="step === 2"
          key="s2"
          class="flex flex-col flex-1 gap-5 lg:gap-8"
        >
          <div>
            <h2 class="text-brand-text text-xl font-bold">
              Cuéntanos sobre el inmueble
            </h2>
            <p class="text-brand-muted text-sm mt-1">
              Las características que determinan el valor.
            </p>
          </div>

          <!-- Área + año -->
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <label
                class="text-xs font-semibold text-brand-muted uppercase tracking-wide"
                >Área construida</label
              >
              <div class="relative">
                <input
                  v-model.number="form.area_m2"
                  type="number"
                  min="1"
                  max="2000"
                  placeholder="120"
                  class="w-full border border-brand-border rounded-xl px-4 py-3 pr-10 text-sm text-brand-text placeholder-brand-placeholder focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent"
                />
                <span
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-brand-muted text-xs font-medium pointer-events-none"
                  >m²</span
                >
              </div>
            </div>
            <div class="flex flex-col gap-1.5">
              <label
                class="text-xs font-semibold text-brand-muted uppercase tracking-wide"
              >
                Año
                <span class="text-brand-placeholder font-normal normal-case"
                  >(opcional)</span
                >
              </label>
              <input
                v-model.number="form.year_built"
                type="number"
                min="1900"
                max="2100"
                placeholder="2006"
                class="w-full border border-brand-border rounded-xl px-4 py-3 text-sm text-brand-text placeholder-brand-placeholder focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent"
              />
            </div>
          </div>

          <!-- Steppers -->
          <div class="grid grid-cols-3 gap-3">
            <div
              v-for="f in stepperFields"
              :key="f.key"
              class="flex flex-col gap-1.5"
            >
              <label
                class="text-xs font-semibold text-brand-muted uppercase tracking-wide"
                >{{ f.label }}</label
              >
              <div
                class="flex items-center border border-brand-border rounded-xl overflow-hidden"
              >
                <button
                  @click="decrement(f.key, f.inc, f.min)"
                  class="px-3 py-3 text-brand-muted hover:bg-brand-bg transition-colors text-sm font-bold leading-none"
                >
                  −
                </button>
                <span
                  class="flex-1 text-center text-sm font-semibold text-brand-text select-none"
                >
                  {{ form[f.key] }}
                </span>
                <button
                  @click="increment(f.key, f.inc, f.max)"
                  class="px-3 py-3 text-brand-muted hover:bg-brand-bg transition-colors text-sm font-bold leading-none"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          <!-- Estrato -->
          <div class="flex flex-col gap-1.5">
            <label
              class="text-xs font-semibold text-brand-muted uppercase tracking-wide"
              >Estrato</label
            >
            <div class="flex gap-2">
              <button
                v-for="s in [1, 2, 3, 4, 5, 6]"
                :key="s"
                @click="form.stratum = s"
                class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200"
                :class="
                  form.stratum === s
                    ? 'bg-brand-primary text-white shadow-sm'
                    : 'border border-brand-border text-brand-muted hover:border-brand-primary hover:text-brand-primary'
                "
              >
                {{ s }}
              </button>
            </div>
          </div>
        </div>

        <!-- STEP 3: Ubicación -->
        <div v-else-if="step === 3" key="s3" class="flex flex-col flex-1 gap-5">
          <div>
            <h2 class="text-brand-text text-xl font-bold">
              ¿Dónde está ubicado?
            </h2>
            <p class="text-brand-muted text-sm mt-1">
              Escribe la dirección para detectar el barrio automáticamente.
            </p>
          </div>

          <!-- GMaps Places Autocomplete -->
          <div class="flex flex-col gap-1.5">
            <label
              class="text-xs font-semibold text-brand-muted uppercase tracking-wide"
              >Dirección del inmueble</label
            >
            <div ref="autocompleteContainer" class="w-full" />
          </div>

          <!-- Barrio detectado (mock) -->
          <div
            v-if="neighborhood"
            class="flex items-center gap-3 p-4 rounded-2xl bg-brand-primary-light border border-brand-primary/20"
          >
            <div
              class="w-8 h-8 rounded-full bg-brand-primary flex items-center justify-center flex-shrink-0"
            >
              <svg
                class="w-4 h-4 text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
                />
              </svg>
            </div>
            <div>
              <p
                class="text-xs font-semibold text-brand-muted uppercase tracking-wide"
              >
                Barrio detectado
              </p>
              <p class="text-sm font-bold text-brand-text">
                {{ neighborhood }} <span class="text-brand-primary">✓</span>
              </p>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Navigation -->
    <div
      class="flex items-center justify-between mt-auto pt-4 border-t border-brand-divider"
    >
      <button
        v-if="step > 1"
        @click="step--"
        class="text-sm text-brand-muted font-semibold hover:text-brand-text transition-colors"
      >
        ← Atrás
      </button>
      <span v-else />

      <button
        v-if="step < 3"
        @click="nextStep"
        :disabled="!canAdvance"
        class="px-8 py-3 rounded-full text-sm font-semibold transition-all duration-200"
        :class="
          canAdvance
            ? 'bg-brand-primary text-white hover:bg-green-500 shadow-sm'
            : 'bg-brand-divider text-brand-placeholder cursor-not-allowed'
        "
      >
        Continuar
      </button>

      <button
        v-else
        @click="onSubmit"
        :disabled="!canAdvance"
        class="px-8 py-3 rounded-full text-sm font-semibold transition-all duration-200"
        :class="
          canAdvance
            ? 'bg-brand-primary text-white hover:bg-green-500 shadow-sm'
            : 'bg-brand-divider text-brand-placeholder cursor-not-allowed'
        "
      >
        Ver avalúo →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, useTemplateRef, watch } from "vue";
import {
  useAvmForm,
  type AvmFormPayload,
  type SelectedPlace,
} from "@/composables/useAvmForm";
import { getNeighborhood } from "@/composables/Location";

const emit = defineEmits<{
  submit: [
    data: {
      payload: AvmFormPayload;
      place: SelectedPlace;
      neighborhood: string;
    }
  ];
  "place-selected": [data: { place: SelectedPlace }];
}>();

const autocompleteContainer = useTemplateRef<HTMLDivElement>(
  "autocompleteContainer"
);

const neighborhood = ref<string | null>(null);

const {
  step,
  form,
  stepLabels,
  stepperFields,
  place,
  canAdvance,
  nextStep,
  increment,
  decrement,
  toPayload,
} = useAvmForm(autocompleteContainer);

watch(place, async (val) => {
  if (!val) return;
  emit("place-selected", { place: val });
  neighborhood.value = await getNeighborhood(val.latitude, val.longitude);
});

function onSubmit() {
  const payload = toPayload();
  if (payload && place.value && neighborhood.value)
    emit("submit", {
      payload,
      place: place.value,
      neighborhood: neighborhood.value,
    });
}
</script>

<style scoped>
/* Step transitions — slide horizontal */
.step-enter-active,
.step-leave-active {
  transition: all 0.22s ease-in-out;
}
.step-enter-from {
  opacity: 0;
  transform: translateX(16px);
}
.step-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}
</style>
