<template>
  <div class="min-h-screen bg-brand-bg">
    <div class="w-full px-[5%] sm:px-[8%] lg:px-[10%] py-8">
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
          <PropertyPhotosCard :property="property" />
        </div>

        <!-- Columna derecha: información y detalles editables -->
        <div class="w-full lg:w-1/2 flex flex-col gap-8">
          <PropertyInfoCard :property="property" />
          <PropertyEditForm :form="form" @update:form="form = $event" />
          <PropertyEditActions
            @back="router.push('/properties')"
            @save="handleSave"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import PropertyHeaderCard from "@/components/properties/edit/PropertyHeaderCard.vue";
import PropertyPhotosCard from "@/components/properties/edit/PropertyPhotosCard.vue";
import PropertyInfoCard from "@/components/properties/edit/PropertyInfoCard.vue";
import PropertyEditForm from "@/components/properties/edit/PropertyEditForm.vue";
import PropertyEditActions from "@/components/properties/edit/PropertyEditActions.vue";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import { buildNeighborhoodMap } from "@/composables/catalog/useNeighborhoodLookup";
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

const form = ref<EditForm>({
  condition: "used",
  currency: "COP",
  price: 0,
  admin_fee: null,
  description: "",
});

onMounted(async () => {
  const { data } = await propertiesApi.get<PropertyDetail>(
    PROPERTIES_ENDPOINTS.byId(propertyId.value)
  );
  property.value = data;

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

// TODO: reemplazar por PATCH /v1/properties/{id} cuando se cablee el update real
function handleSave() {
  console.log("Guardar (mock):", form.value);
}
</script>
