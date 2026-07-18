<template>
  <div class="min-h-screen bg-brand-bg">
    <PageContainer class="w-full py-8">
      <h1 class="text-brand-text text-2xl font-bold mb-1">Editar propiedad</h1>
      <p class="text-brand-muted text-sm mb-8">
        Los datos estructurales no se pueden modificar luego de publicar.
      </p>

      <div v-if="isLoading" class="flex items-center justify-center py-20">
        <BaseSpinner class="h-8 w-8 text-brand-primary" />
      </div>

      <div v-else class="flex flex-col lg:flex-row gap-8">
        <!-- Columna izquierda: la propiedad -->
        <div class="w-full lg:w-1/2 flex flex-col gap-8">
          <PropertyHeaderCard
            :property="property"
            :location-label="locationLabel"
          />
          <PropertyPhotosCard
            :property="property"
            @add-photos="showUploadModal = true"
            @delete-photos="showDeleteModal = true"
          />

          <UploadPropertyImagesModal
            v-model="showUploadModal"
            :property-id="property?.id ?? ''"
            :images-allowed="imagesAllowed"
            :has-existing-photos="!!property?.images.length"
            @success="fetchProperty"
          />

          <DeletePropertyImagesModal
            v-model="showDeleteModal"
            :property-id="property?.id ?? ''"
            :images="property?.images ?? []"
            @success="fetchProperty"
          />
        </div>

        <!-- Columna derecha: información y detalles editables -->
        <div class="w-full lg:w-1/2 flex flex-col gap-8">
          <PropertyInfoCard :property="property" />
          <PropertyEditForm :form="form" @update:form="form = $event" />
          <p v-if="saveError" class="text-sm text-red-600 -mt-4">
            {{ saveError }}
          </p>
          <PropertyEditActions
            @back="router.push('/properties')"
            @save="handleSave"
          />
        </div>
      </div>
    </PageContainer>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import PageContainer from "@/components/shared/PageContainer.vue";
import PropertyHeaderCard from "@/components/properties/edit/PropertyHeaderCard.vue";
import PropertyPhotosCard from "@/components/properties/edit/PropertyPhotosCard.vue";
import UploadPropertyImagesModal from "@/components/properties/edit/UploadPropertyImagesModal.vue";
import DeletePropertyImagesModal from "@/components/properties/edit/DeletePropertyImagesModal.vue";
import PropertyInfoCard from "@/components/properties/edit/PropertyInfoCard.vue";
import PropertyEditForm from "@/components/properties/edit/PropertyEditForm.vue";
import PropertyEditActions from "@/components/properties/edit/PropertyEditActions.vue";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import { buildNeighborhoodMap } from "@/composables/catalog/useNeighborhoodLookup";
import { LIMITS } from "@/config";
import type {
  PropertyDetail,
  PropertyEditForm as EditForm,
} from "@/types/properties";

const route = useRoute();
const router = useRouter();
const propertyId = computed(() => route.params.id as string);

const isLoading = ref(true);
const property = ref<PropertyDetail | null>(null);
const locationLabel = ref("");
const saveError = ref<string | null>(null);

const showUploadModal = ref(false);
const showDeleteModal = ref(false);
const imagesAllowed = computed(
  () => LIMITS.MAX_IMAGES_PER_PROPERTY - (property.value?.images.length ?? 0)
);

const form = ref<EditForm>({
  condition: "used",
  currency: "COP",
  price: 0,
  admin_fee: null,
  description: "",
});

async function fetchProperty() {
  const { data } = await propertiesApi.get<PropertyDetail>(
    PROPERTIES_ENDPOINTS.byId(propertyId.value)
  );
  property.value = data;
  return data;
}

onMounted(async () => {
  const data = await fetchProperty();

  form.value = {
    condition: data.condition,
    currency: data.currency,
    price: Number(data.price),
    admin_fee: data.admin_fee !== null ? Number(data.admin_fee) : null,
    description: data.description ?? "",
  };

  if (data.location) {
    const neighborhoodMap = await buildNeighborhoodMap([data.location.city_id]);
    locationLabel.value = neighborhoodMap[data.location.neighborhood_id] ?? "";
  }

  isLoading.value = false;
});

function validateForm(): string | null {
  if (!form.value.price || form.value.price <= 0) {
    return "El precio debe ser mayor a 0";
  }
  if (form.value.admin_fee !== null && form.value.admin_fee < 0) {
    return "La administración no puede ser negativa";
  }
  return null;
}

async function handleSave() {
  saveError.value = validateForm();
  if (saveError.value) return;

  try {
    await propertiesApi.patch(
      PROPERTIES_ENDPOINTS.byId(propertyId.value),
      form.value
    );
    router.push("/properties");
  } catch (error) {
    console.error("Error al guardar los cambios:", error);
    saveError.value = "No se pudo guardar los cambios. Intenta de nuevo.";
  }
}
</script>
