<template>
  <div class="bg-brand-bg min-h-screen">
    <div class="px-[5%] sm:px-[8%] lg:px-[10%] py-12">
      <!-- Header -->
      <div class="mb-8 flex flex-col gap-1">
        <span
          class="text-brand-muted text-xs font-semibold uppercase tracking-widest"
          >Avalúo inteligente</span
        >
        <h1 class="text-brand-text text-3xl lg:text-4xl font-bold">
          ¿Cuánto vale tu inmueble?
        </h1>
        <p class="text-brand-muted text-sm max-w-md leading-relaxed">
          Resultado en segundos. Entrenado con más de
          <strong class="text-brand-text font-semibold"
            >53.000 propiedades</strong
          >
          en Bogotá.
        </p>
      </div>

      <!-- 50/50 layout -->
      <div class="flex flex-col md:flex-row gap-6 items-stretch min-h-[72vh]">
        <!-- LEFT: form card -->
        <div class="w-full md:w-1/2">
          <div
            class="bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.08)] h-full p-8 lg:p-12 flex flex-col"
          >
            <Transition name="panel" mode="out-in">
              <!-- RESULT -->
              <div
                v-if="showResult"
                key="result"
                class="flex flex-col items-center justify-center flex-1 gap-6 text-center"
              >
                <span
                  class="text-brand-muted text-xs font-semibold uppercase tracking-widest"
                  >Valor estimado</span
                >
                <div class="flex flex-col gap-1">
                  <p
                    class="text-brand-text text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight tracking-tight"
                  >
                    {{ formatCOP(tweened.value) }}
                  </p>
                  <p class="text-brand-muted text-sm">pesos colombianos</p>
                </div>
                <div class="flex flex-col gap-1.5 text-sm text-brand-muted">
                  <span>± 11% error medio del modelo</span>
                  <span>
                    Barrio: <strong class="text-brand-text">EL NOGAL</strong> ·
                    Estrato 5
                  </span>
                  <span class="text-xs text-brand-placeholder"
                    >bogota-avm · v1</span
                  >
                </div>
                <button
                  @click="reset"
                  class="mt-2 text-sm text-brand-primary font-semibold hover:underline transition-colors"
                >
                  ← Calcular de nuevo
                </button>
              </div>

              <!-- FORM -->
              <div v-else key="form" class="flex flex-col flex-1 gap-6">
                <!-- Step indicator -->
                <div class="flex items-center">
                  <template v-for="(label, i) in stepLabels" :key="i">
                    <div class="flex flex-col items-center">
                      <div
                        class="w-3 h-3 rounded-full transition-colors duration-300"
                        :class="
                          step >= i + 1
                            ? 'bg-brand-primary'
                            : 'bg-brand-divider'
                        "
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
                      :class="
                        step >= i + 2 ? 'bg-brand-primary' : 'bg-brand-divider'
                      "
                    />
                  </template>
                </div>

                <!-- Step content -->
                <div class="flex flex-col flex-1">
                  <Transition name="step" mode="out-in">
                    <!-- STEP 1: Tipo -->
                    <div
                      v-if="step === 1"
                      key="s1"
                      class="flex flex-col flex-1"
                    >
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
                            <path
                              d="M5 10v10a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1V10"
                            />
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
                            <span
                              class="text-brand-placeholder font-normal normal-case"
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
                    <div
                      v-else-if="step === 3"
                      key="s3"
                      class="flex flex-col flex-1 gap-5"
                    >
                      <div>
                        <h2 class="text-brand-text text-xl font-bold">
                          ¿Dónde está ubicado?
                        </h2>
                        <p class="text-brand-muted text-sm mt-1">
                          Escribe la dirección para detectar el barrio
                          automáticamente.
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
                            EL NOGAL <span class="text-brand-primary">✓</span>
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
                    @click="submit"
                    class="px-8 py-3 bg-brand-primary text-white rounded-full text-sm font-semibold hover:bg-green-500 transition-all duration-200 shadow-sm"
                  >
                    Ver avalúo →
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </div>

        <!-- RIGHT: map mock -->
        <div class="w-full md:w-1/2 md:pl-[5%]">
          <div
            class="rounded-3xl bg-brand-dark h-full min-h-[360px] relative overflow-hidden flex flex-col items-center justify-center"
          >
            <!-- dot grid -->
            <div
              class="absolute inset-0 opacity-10"
              style="
                background-image: radial-gradient(
                  circle,
                  #22c55e 1px,
                  transparent 1px
                );
                background-size: 24px 24px;
              "
            />

            <!-- pin placeholder -->
            <div
              class="relative z-10 flex flex-col items-center gap-3 text-center"
            >
              <div
                class="w-14 h-14 rounded-full bg-brand-primary/20 border border-brand-primary/30 flex items-center justify-center"
              >
                <svg
                  class="w-7 h-7 text-brand-primary"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
                  />
                </svg>
              </div>
              <div class="flex flex-col gap-0.5">
                <p
                  class="text-white/50 text-xs font-semibold uppercase tracking-widest"
                >
                  Mapa interactivo
                </p>
                <p class="text-white/25 text-xs">Leaflet · aquí va el mapa</p>
              </div>
            </div>

            <!-- coords bar -->
            <div class="absolute bottom-5 left-5 right-5">
              <div
                class="bg-white/5 border border-white/10 rounded-2xl px-5 py-3"
              >
                <p class="text-white/35 text-xs font-mono">
                  4.6625749, -74.0495009 · EL NOGAL
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from "vue";
import gsap from "gsap";

/* eslint-disable @typescript-eslint/no-explicit-any */
declare const google: any;

const step = ref(1);
const showResult = ref(false);
const autocompleteContainer = ref<HTMLDivElement | null>(null);

watch(step, async (val) => {
  if (val !== 3) return;
  await nextTick();
  await new Promise((r) => setTimeout(r, 260));
  const { PlaceAutocompleteElement } = await google.maps.importLibrary(
    "places"
  );
  const el = new PlaceAutocompleteElement({});
  autocompleteContainer.value?.appendChild(el);
  el.addEventListener("gmp-placeselect", (e: any) => {
    const place = e.place;
    console.log("lat:", place.location?.lat(), "lng:", place.location?.lng());
  });
});
const stepLabels = ["Tipo", "Detalles", "Ubicación"];

const form = reactive({
  property_type: "apartment" as "apartment" | "house",
  area_m2: null as number | null,
  bedrooms: 3,
  bathrooms: 2,
  parking_spots: 1,
  stratum: 3,
  year_built: null as number | null,
});

const tweened = reactive({ value: 0 });

const stepperFields = [
  { key: "bedrooms" as const, label: "Habitaciones", inc: 1, min: 0, max: 20 },
  { key: "bathrooms" as const, label: "Baños", inc: 0.5, min: 0, max: 20 },
  {
    key: "parking_spots" as const,
    label: "Parqueaderos",
    inc: 1,
    min: 0,
    max: 10,
  },
];

type StepperKey = "bedrooms" | "bathrooms" | "parking_spots";

function increment(key: StepperKey, inc: number, max: number) {
  if (form[key] < max) form[key] = Math.round((form[key] + inc) * 10) / 10;
}

function decrement(key: StepperKey, inc: number, min: number) {
  if (form[key] > min) form[key] = Math.round((form[key] - inc) * 10) / 10;
}

const canAdvance = computed(() => {
  if (step.value === 2) return !!form.area_m2 && form.area_m2 > 0;
  return true;
});

function nextStep() {
  if (canAdvance.value) step.value++;
}

function submit() {
  showResult.value = true;
  gsap.to(tweened, { duration: 1.5, value: 580_000_000, ease: "power2.out" });
}

function reset() {
  showResult.value = false;
  step.value = 1;
  tweened.value = 0;
}

function formatCOP(value: number): string {
  return "$ " + Math.round(value).toLocaleString("es-CO");
}
</script>

<style scoped>
/* Form ↔ result — ease in/out fade + scale */
.panel-enter-active,
.panel-leave-active {
  transition: all 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}
.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: scale(0.97);
}

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
