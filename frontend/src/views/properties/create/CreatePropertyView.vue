<template>
  <div class="w-full px-[5%] sm:px-[8%] lg:px-[10%] py-10">
    <div
      class="bg-white border border-brand-divider rounded-2xl overflow-hidden"
    >
      <StepIndicator :steps="steps" :current="currentStep" />

      <div class="flex min-h-[520px]">
        <div
          :class="
            currentStep >= 2
              ? 'w-full p-8'
              : 'flex-1 p-8 border-r border-brand-divider'
          "
        >
          <StepTipo
            v-if="currentStep === 0"
            :form="form"
            :attempted="attempted"
            @update:form="form = $event"
          />
          <StepDetalles
            v-if="currentStep === 1"
            :form="form"
            :attempted="attempted"
            @update:form="form = $event"
          />
          <StepUbicacion
            v-if="currentStep === 2"
            :form="form"
            :attempted="attempted"
            :neighborhood-name="neighborhoodName"
            :selected-place="selectedPlace"
            @update:form="form = $event"
            @update:neighborhoodName="neighborhoodName = $event"
            @update:selectedPlace="selectedPlace = $event"
          />

          <!-- Step 3: error state o imágenes -->
          <div v-if="currentStep === 3">
            <div
              v-if="error"
              class="max-w-lg mx-auto py-6 flex flex-col items-center gap-5"
            >
              <div
                class="w-full rounded-2xl border border-orange-200 bg-orange-50 p-8 flex flex-col items-center text-center gap-5"
              >
                <div
                  class="w-14 h-14 rounded-full bg-orange-100 flex items-center justify-center"
                >
                  <AlertTriangle class="w-7 h-7 text-orange-500" />
                </div>

                <div class="space-y-1.5">
                  <p class="text-base font-bold text-brand-text">
                    No pudimos publicar tu propiedad
                  </p>
                  <p class="text-sm text-brand-muted">
                    Tu información sigue aquí. Puedes volver a editar o
                    reintentar en unos minutos.
                  </p>
                </div>

                <div
                  class="w-full text-left bg-white rounded-xl border border-orange-100 px-4 py-3"
                >
                  <p
                    class="text-xs font-semibold text-brand-muted uppercase tracking-wide mb-2"
                  >
                    Posibles causas
                  </p>
                  <ul
                    class="text-sm text-brand-muted space-y-1 list-disc list-inside"
                  >
                    <li>Un problema temporal del servidor</li>
                    <li>Una conexión inestable</li>
                    <li>Un inconveniente con alguno de los datos enviados</li>
                  </ul>
                </div>

                <p v-if="errorCode" class="text-xs text-brand-muted font-mono">
                  Código: {{ errorCode }}
                </p>
              </div>

              <a
                href="mailto:soporte@side.com"
                class="text-sm text-brand-primary font-medium underline underline-offset-2"
              >
                ¿El problema continúa? Contactar soporte
              </a>
            </div>
            <StepImagenes v-else v-model="selectedFiles" />
          </div>
        </div>
        <CreateSummary v-if="currentStep < 2" :form="form" />
      </div>

      <div
        class="flex justify-between items-center px-8 py-5 border-t border-brand-divider"
      >
        <button
          v-if="currentStep > 0"
          @click="currentStep--"
          :disabled="currentStep === 3 && !error"
          class="px-5 py-2 rounded-xl border border-brand-border text-sm font-medium text-brand-text hover:bg-brand-bg transition disabled:opacity-40 disabled:cursor-not-allowed"
        >
          ← Volver a editar
        </button>
        <div v-else />
        <!-- Botón paso 3 sin error: Publicar con upload -->
        <button
          v-if="currentStep === 3 && !error"
          @click="upload()"
          :disabled="uploadLoading || selectedFiles.length === 0"
          class="px-7 py-2.5 rounded-xl text-white text-sm font-bold transition-all duration-200 hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center gap-2"
          style="
            background: linear-gradient(90deg, #22c55e, #16a34a);
            box-shadow: 0 8px 24px rgba(34, 197, 94, 0.35);
          "
        >
          <BaseSpinner v-if="uploadLoading" class="w-4 h-4" />
          {{ uploadLoading ? "Publicando..." : "Publicar" }}
        </button>

        <!-- Botón resto de pasos -->
        <button
          v-else
          @click="handleNext()"
          :disabled="loading"
          class="px-7 py-2.5 rounded-xl text-white text-sm font-bold transition-all duration-200 hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:translate-y-0"
          style="
            background: linear-gradient(90deg, #22c55e, #16a34a);
            box-shadow: 0 8px 24px rgba(34, 197, 94, 0.35);
          "
        >
          {{
            loading
              ? "Publicando..."
              : currentStep === 3 && error
              ? "Reintentar →"
              : currentStep === 2
              ? "Publicar →"
              : "Siguiente →"
          }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { AlertTriangle } from "@lucide/vue";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import StepIndicator from "@/components/properties/create/StepIndicator.vue";
import StepTipo from "@/components/properties/create/StepTipo.vue";
import StepDetalles from "@/components/properties/create/StepDetalles.vue";
import StepUbicacion from "@/components/properties/create/StepUbicacion.vue";
import StepImagenes from "@/components/properties/create/StepImagenes.vue";
import CreateSummary from "@/components/properties/create/CreateSummary.vue";
import { useCreatePropertyForm } from "@/composables/properties/useCreatePropertyForm";
import { useImageUpload } from "@/composables/properties/useImageUpload";

const steps = ["Tipo y condición", "Detalles", "Ubicación", "Imágenes"];
const currentStep = ref(0);

const {
  form,
  loading,
  error,
  errorCode,
  attempted,
  neighborhoodName,
  selectedPlace,
  createListing,
} = useCreatePropertyForm();

const {
  loading: uploadLoading,
  error: uploadError,
  uploadImages,
} = useImageUpload();

const propertyId = ref<string | null>(null);
const selectedFiles = ref<File[]>([]);

function isStepValid(step: number): boolean {
  const f = form.value;
  if (step === 0)
    return (
      !!f.property_type &&
      !!f.listing_type &&
      !!f.condition &&
      !!f.area_m2 &&
      !!f.bedrooms &&
      !!f.bathrooms
    );
  if (step === 1) {
    const floorOk =
      f.property_type === "apartment"
        ? f.floor_number !== null
        : f.total_floors !== null;
    return !!f.price && floorOk;
  }
  if (step === 2) return !!f.location.neighborhood_id;
  return true;
}

function handleNext() {
  if (currentStep.value === 2 || (currentStep.value === 3 && error.value)) {
    submitAndContinue();
    return;
  }
  if (!isStepValid(currentStep.value)) {
    attempted.value = true;
    return;
  }
  attempted.value = false;
  currentStep.value++;
}

async function submitAndContinue() {
  try {
    propertyId.value = await createListing(form.value);
  } catch {
  } finally {
    currentStep.value = 3;
  }
}

async function upload() {
  await uploadImages(selectedFiles.value, propertyId.value!);
  selectedFiles.value = [];
}
</script>
