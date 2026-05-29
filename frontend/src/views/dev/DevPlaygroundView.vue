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
              <AvmResult
                v-if="showResult"
                key="result"
                :price="price"
                :barrio="barrio"
                :estrato="estrato"
                @reset="reset"
              />

              <!-- FORM -->
              <AvmForm v-else key="form" @submit="onSubmit" />
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
import { ref } from "vue";

import AvmForm from "@/components/avm/AvmForm.vue";
import AvmResult from "@/components/avm/AvmResult.vue";
import type { AvmFormPayload, SelectedPlace } from "@/composables/useAvmForm";

const showResult = ref(false);
const price = ref(0);
const barrio = ref("");
const estrato = ref(0);

function onSubmit(data: { payload: AvmFormPayload; place: SelectedPlace }) {
  // TODO (#6): chain catalog by-coords (place.lat/lon → barrio) + POST /predict
  console.log("avm submit", data);
  estrato.value = data.payload.stratum;
  barrio.value = "EL NOGAL"; // placeholder: vendrá de catalog by-coords
  price.value = 580_000_000; // placeholder hasta cablear /predict
  showResult.value = true;
}

function reset() {
  showResult.value = false;
  price.value = 0;
  barrio.value = "";
  estrato.value = 0;
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
</style>
