<template>
  <div class="flex flex-col gap-6">

    <!-- Top: address search -->
    <div>
      <h2 class="text-brand-text text-xl font-bold mb-1">Ubicación</h2>
      <p class="text-brand-muted text-sm mb-6">Busca la dirección exacta de la propiedad.</p>

      <div class="mb-4">
        <label class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3">Dirección</label>
      </div>

      <div class="flex gap-3">
        <!-- Búsqueda: 3/4 -->
        <div class="w-3/4">
          <div ref="autocompleteContainer" class="w-full" />
        </div>

        <!-- Barrio detectado: 1/4 -->
        <div class="w-1/4">
          <div v-if="neighborhood" class="h-full flex items-center gap-3 p-4 rounded-2xl bg-brand-primary-light border border-brand-primary/20">
            <div class="w-8 h-8 rounded-full bg-brand-primary flex items-center justify-center shrink-0">
              <MapPin class="w-4 h-4 text-white" />
            </div>
            <div>
              <p class="text-xs font-semibold text-brand-muted uppercase tracking-wide">Barrio</p>
              <p class="text-sm font-bold text-brand-text">{{ neighborhood }} <span class="text-brand-primary">✓</span></p>
            </div>
          </div>
          <div v-else class="h-full flex items-center justify-center border-2 border-dashed border-brand-divider rounded-2xl p-4">
            <p class="text-xs text-brand-muted text-center">Barrio detectado automáticamente</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom: NearbyPlaces full width -->
    <div>
      <NearbyPlaces
        v-if="selectedPlace"
        :lat="selectedPlace.latitude"
        :lon="selectedPlace.longitude"
        :property-id="previewId"
      />
      <div v-else class="h-64 bg-brand-bg rounded-2xl border-2 border-dashed border-brand-divider flex flex-col items-center justify-center gap-3 px-8 text-center">
        <div class="flex gap-4 text-brand-muted/30">
          <MapPin class="w-8 h-8" />
          <Navigation class="w-8 h-8" />
          <Coffee class="w-8 h-8" />
        </div>
        <p class="text-sm font-semibold text-brand-text">Descubre qué hay cerca de tu propiedad</p>
        <p class="text-xs text-brand-muted">Al ingresar la dirección verás un mapa con colegios, hospitales, restaurantes, transporte y más — todo lo que le importa a un comprador o arrendatario.</p>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from "vue";
import { MapPin, Navigation, Coffee } from "@lucide/vue";
import NearbyPlaces from "@/components/properties/detail/NearbyPlaces.vue";
import { getNeighborhood } from "@/composables/catalog/useLocation";
import type { CreatePropertyForm } from "@/types/properties";
import type { SelectedPlace } from "@/composables/avm/useAvmForm";

declare const google: any;

const props = defineProps<{ form: CreatePropertyForm }>();
const emit = defineEmits<{ (e: "update:form", v: CreatePropertyForm): void }>();

const autocompleteContainer = ref<HTMLDivElement | null>(null);
const selectedPlace = ref<SelectedPlace | null>(null);
const neighborhood = ref<string | null>(null);
const previewId = crypto.randomUUID();

onMounted(async () => {
  await nextTick();
  const { PlaceAutocompleteElement } = await google.maps.importLibrary("places");
  const el = new PlaceAutocompleteElement({});
  autocompleteContainer.value?.appendChild(el);

  el.addEventListener("gmp-select", async (e: any) => {
    const p = e.placePrediction.toPlace();
    await p.fetchFields({ fields: ["displayName", "formattedAddress", "location"] });

    const lat = p.location?.lat();
    const lon = p.location?.lng();

    selectedPlace.value = { latitude: lat, longitude: lon, address: p.formattedAddress ?? "" };
    neighborhood.value = (await getNeighborhood(lat, lon)) ?? null;

    emit("update:form", {
      ...props.form,
      location: { ...props.form.location, latitude: lat, longitude: lon },
    });
  });
});
</script>
