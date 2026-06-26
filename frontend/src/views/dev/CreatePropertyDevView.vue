<template>
  <div class="w-full px-[5%] sm:px-[8%] lg:px-[10%] py-10">
    <div class="bg-white border border-brand-divider rounded-2xl overflow-hidden">

      <StepIndicator :steps="steps" :current="currentStep" />

      <div class="flex min-h-[520px]">
        <div :class="currentStep === 2 ? 'w-full p-8' : 'flex-1 p-8 border-r border-brand-divider'">
          <StepTipo      v-if="currentStep === 0" :form="form" @update:form="form = $event" />
          <StepDetalles  v-if="currentStep === 1" :form="form" @update:form="form = $event" />
          <StepUbicacion v-if="currentStep === 2" :form="form" @update:form="form = $event" />
        </div>
        <CreateSummary v-if="currentStep !== 2" :form="form" />
      </div>

      <div class="flex justify-between items-center px-8 py-5 border-t border-brand-divider">
        <button
          v-if="currentStep > 0"
          @click="currentStep--"
          class="px-5 py-2 rounded-xl border border-brand-border text-sm font-medium text-brand-text hover:bg-brand-bg transition"
        >← Anterior</button>
        <div v-else />
        <button
          @click="currentStep++"
          class="px-7 py-2.5 rounded-xl text-white text-sm font-bold transition-all duration-200 hover:-translate-y-0.5"
          style="background: linear-gradient(90deg, #22C55E, #16A34A); box-shadow: 0 8px 24px rgba(34,197,94,0.35);"
        >Siguiente →</button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import StepIndicator from "@/components/properties/create/StepIndicator.vue";
import StepTipo from "@/components/properties/create/StepTipo.vue";
import StepDetalles from "@/components/properties/create/StepDetalles.vue";
import StepUbicacion from "@/components/properties/create/StepUbicacion.vue";
import CreateSummary from "@/components/properties/create/CreateSummary.vue";
import type { CreatePropertyForm } from "@/types/properties";

const steps = ["Tipo y condición", "Detalles", "Ubicación", "Imágenes"];
const currentStep = ref(0);

const form = ref<CreatePropertyForm>({
  property_type: "",
  listing_type: "",
  condition: "",
  currency: "COP",
  area_m2: null,
  bedrooms: null,
  bathrooms: null,
  parking_spots: 0,
  price: null,
  admin_fee: null,
  floor_number: null,
  total_floors: null,
  description: "",
  year_built: null,
  stratum: null,
  location: {
    neighborhood_id: "",
    city_id: "",
    country_id: "",
    latitude: null,
    longitude: null,
  },
});
</script>
