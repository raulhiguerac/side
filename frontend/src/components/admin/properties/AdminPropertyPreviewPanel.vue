<template>
  <div class="overflow-hidden rounded-2xl border border-brand-divider bg-white">
    <div class="border-b border-brand-divider px-5 py-4">
      <h2 class="text-brand-text text-sm font-semibold">Vista previa</h2>
      <p class="text-brand-muted mt-0.5 text-xs">
        Lo que ve un usuario en el detalle público.
      </p>
    </div>

    <p
      v-if="!propertyId"
      class="text-brand-muted px-5 py-12 text-center text-sm"
    >
      Seleccioná una propiedad de la tabla.
    </p>

    <div v-else-if="loading" class="flex justify-center px-5 py-12">
      <BaseSpinner class="h-6 w-6 text-brand-primary" />
    </div>

    <p
      v-else-if="error"
      class="m-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
    >
      {{ error }}
    </p>

    <div v-else-if="property" class="space-y-5 p-5">
      <!--
        Portada sola en vez de `PropertyPhotoGrid`: esa grilla reparte 5 fotos
        en 4 columnas y a este ancho quedarían miniaturas ilegibles. El resto se
        ve en el popup, que es el mismo que usa el detalle público.
      -->
      <button
        v-if="cover"
        type="button"
        @click="isGalleryOpen = true"
        class="group relative block h-48 w-full overflow-hidden rounded-xl"
      >
        <img
          :src="cover.url"
          alt="Foto de portada"
          class="h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.03]"
        />
        <span
          v-if="property.images.length > 1"
          class="absolute bottom-2 right-2 rounded-lg bg-black/60 px-2 py-1 text-xs font-medium text-white"
        >
          +{{ property.images.length - 1 }} fotos
        </span>
      </button>

      <div
        v-else
        class="flex h-48 items-center justify-center rounded-xl bg-brand-bg"
      >
        <p class="text-brand-placeholder text-sm">Sin fotos</p>
      </div>

      <PropertyOverview
        :title="title"
        :location-label="locationLabel"
        :status-label="statusLabel"
        :status-style="statusStyle"
        :verification-label="verificationLabel"
        :verification-style="verificationStyle"
        :formatted-price="formattedPrice"
        :formatted-admin-fee="formattedAdminFee"
        :has-admin-fee="hasAdminFee"
        :description="description"
        :stats="stats"
        :details="details"
      />
    </div>

    <!--
      Sin `NearbyPlaces` a propósito: fetchea en su `onMounted`, así que montarlo
      acá dispararía 9 isócronas contra ORS en cada click de fila, para un dato
      que no se usa para moderar. Si algún día se agrega, va detrás de un `v-if`
      cerrado — con `v-show` el componente se monta igual y el costo se paga.
    -->

    <PhotoGalleryPopup
      v-if="property"
      :is-open="isGalleryOpen"
      :images="property.images"
      :start-index="coverIndex"
      @close="isGalleryOpen = false"
    />
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import { buildNeighborhoodMap } from "@/composables/catalog/useNeighborhoodLookup";
import { usePropertyDetail } from "@/composables/properties/usePropertyDetail";
import BaseSpinner from "@/components/shared/BaseSpinner.vue";
import PropertyOverview from "@/components/properties/detail/PropertyOverview.vue";
import PhotoGalleryPopup from "@/components/properties/photos/PhotoGalleryPopup.vue";
import type { PropertyDetail } from "@/types/properties";

const props = defineProps<{ propertyId: string | null }>();

const property = ref<PropertyDetail | null>(null);
const locationLabel = ref("");
const loading = ref(false);
const error = ref<string | null>(null);
const isGalleryOpen = ref(false);

const {
  title,
  formattedPrice,
  formattedAdminFee,
  stats,
  details,
  statusLabel,
  statusStyle,
  verificationLabel,
  verificationStyle,
  hasAdminFee,
  description,
} = usePropertyDetail(property);

const coverIndex = computed(() => {
  const images = property.value?.images ?? [];
  const index = images.findIndex((image) => image.is_cover);
  return index === -1 ? 0 : index;
});

const cover = computed(() => property.value?.images[coverIndex.value] ?? null);

/**
 * Moderar es clickear filas rápido, así que las respuestas se pisan: si se
 * elige A y antes de que llegue se elige B, la respuesta de A puede llegar
 * última y pintar A estando seleccionada B. El token descarta todo lo que no
 * corresponda a la última selección.
 */
let requestToken = 0;

async function load(id: string | null) {
  const token = ++requestToken;

  property.value = null;
  locationLabel.value = "";
  error.value = null;
  isGalleryOpen.value = false;

  if (!id) {
    loading.value = false;
    return;
  }

  loading.value = true;

  try {
    const { data } = await propertiesApi.get<PropertyDetail>(
      PROPERTIES_ENDPOINTS.adminDetail(id)
    );
    if (token !== requestToken) return;
    property.value = data;

    if (data.location) {
      const neighborhoodMap = await buildNeighborhoodMap([
        data.location.city_id,
      ]);
      if (token !== requestToken) return;
      locationLabel.value =
        neighborhoodMap[data.location.neighborhood_id] ?? "";
    }
  } catch (e) {
    if (token !== requestToken) return;
    error.value = "No se pudo cargar la vista previa";
    console.error("admin property preview failed", e);
  } finally {
    if (token === requestToken) loading.value = false;
  }
}

watch(() => props.propertyId, load, { immediate: true });
</script>
