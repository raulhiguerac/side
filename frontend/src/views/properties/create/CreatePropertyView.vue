<template>
  <PageContainer class="w-full py-10">
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
            <StepImagenes
              v-else
              v-model="selectedFiles"
              :max="LIMITS.MAX_IMAGES_PER_PROPERTY"
              :has-existing-photos="false"
            />
          </div>
        </div>
        <CreateSummary v-if="currentStep < 2" :form="form" />
      </div>

      <div
        class="flex justify-between items-center px-8 py-5 border-t border-brand-divider"
      >
        <BaseButton
          v-if="currentStep > 0"
          variant="secondary"
          @click="currentStep--"
          :disabled="currentStep === 3 && !error"
        >
          ← Volver a editar
        </BaseButton>
        <div v-else />
        <!-- Botón paso 3 sin error: Publicar con upload -->
        <BaseButton
          v-if="currentStep === 3 && !error"
          @click="upload()"
          :disabled="selectedFiles.length === 0"
          :loading="uploadLoading"
        >
          {{ uploadLoading ? "Publicando..." : "Publicar" }}
        </BaseButton>

        <!-- Botón resto de pasos -->
        <BaseButton v-else @click="handleNext()" :disabled="loading">
          {{
            loading
              ? "Publicando..."
              : currentStep === 3 && error
              ? "Reintentar →"
              : currentStep === 2
              ? "Publicar →"
              : "Siguiente →"
          }}
        </BaseButton>
      </div>
    </div>
  </PageContainer>
</template>

<script setup lang="ts">
import BaseButton from "@/components/shared/BaseButton.vue";
import { ref } from "vue";
import { useRouter } from "vue-router";
import { AlertTriangle } from "@lucide/vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import StepIndicator from "@/components/properties/create/StepIndicator.vue";
import StepTipo from "@/components/properties/create/StepTipo.vue";
import StepDetalles from "@/components/properties/create/StepDetalles.vue";
import StepUbicacion from "@/components/properties/create/StepUbicacion.vue";
import StepImagenes from "@/components/properties/create/StepImagenes.vue";
import CreateSummary from "@/components/properties/create/CreateSummary.vue";
import { useCreatePropertyForm } from "@/composables/properties/useCreatePropertyForm";
import { useImageUpload } from "@/composables/properties/useImageUpload";
import { LIMITS } from "@/config";

const steps = ["Tipo y condición", "Detalles", "Ubicación", "Imágenes"];
const currentStep = ref(0);
const router = useRouter();

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
    // `createListing` ya dejó el detalle en `error`/`errorCode` y el paso 3 lo renderiza: por eso se avanza igual.
  } finally {
    currentStep.value = 3;
  }
}

async function upload() {
  const success = await uploadImages(selectedFiles.value, propertyId.value!);
  selectedFiles.value = [];
  if (success) router.push("/properties");
}
</script>
