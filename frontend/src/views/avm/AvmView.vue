<template>
  <div class="bg-brand-bg min-h-screen">
    <PageContainer class="py-12">
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
              <AvmForm
                v-else
                key="form"
                @submit="onSubmit"
                @place-selected="onPlaceSelected"
              />
            </Transition>
          </div>
        </div>

        <!-- RIGHT: map -->
        <div class="w-full md:w-1/2 md:pl-[5%]">
          <div
            class="rounded-3xl h-full min-h-[360px] relative overflow-hidden flex flex-col items-center justify-center"
          >
            <MapUser
              :zoom="17"
              :center="center"
              :markers="marker ? [marker] : []"
              :hoveredId="null"
            />
          </div>
        </div>
      </div>
    </PageContainer>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

import AvmForm from "@/components/avm/AvmForm.vue";
import AvmResult from "@/components/avm/AvmResult.vue";
import MapUser from "@/components/map/MapUser.vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import type {
  AvmPredictRequest,
  AvmFormPayload,
  SelectedPlace,
} from "@/composables/avm/useAvmForm";
import type { MarkerData } from "@/types/maps";
import avmApi from "@/api/avmApi";
import { API } from "@/config";

const showResult = ref(false);
const price = ref(0);
const barrio = ref("");
const estrato = ref(0);

const center = ref<[number, number]>([4.681414, -74.046864]);
const marker = ref<MarkerData | null>(null);

function onPlaceSelected(data: { place: SelectedPlace }) {
  center.value = [data.place.latitude, data.place.longitude];
  marker.value = {
    id: "123abc",
    lat: data.place.latitude,
    lon: data.place.longitude,
    imageType: "house",
  };
}

async function onSubmit(data: {
  payload: AvmFormPayload;
  place: SelectedPlace;
  neighborhood: string;
}) {
  const avmPayload: AvmPredictRequest = {
    area_m2: data.payload.area_m2,
    bedrooms: data.payload.bedrooms,
    bathrooms: data.payload.bathrooms,
    parking_spots: data.payload.parking_spots,
    stratum: data.payload.stratum,
    property_type: data.payload.property_type,
    year_built: data.payload.year_built,
    lat: data.place.latitude,
    lon: data.place.longitude,
    barrio_ideca: data.neighborhood,
  };

  estrato.value = data.payload.stratum;
  barrio.value = data.neighborhood;
  try {
    price.value = await fetchPredict(avmPayload);
    showResult.value = true;
  } catch (error) {
    console.error("Error al predecir el precio:", error);
  }
}

async function fetchPredict(payload: AvmPredictRequest): Promise<number> {
  const response = await avmApi.post("/v1/predict", payload);
  return response.data.predicted_price;
}

function reset() {
  showResult.value = false;
  price.value = 0;
  barrio.value = "";
  estrato.value = 0;
}
</script>

<style scoped>
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
