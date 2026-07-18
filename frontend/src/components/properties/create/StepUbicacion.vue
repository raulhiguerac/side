<template>
  <div class="flex flex-col gap-6">
    <!-- Top: address search -->
    <div>
      <h2 class="text-brand-text text-xl font-bold mb-1">Ubicación</h2>
      <p class="text-brand-muted text-sm mb-6">
        Busca la dirección exacta de la propiedad.
      </p>

      <div class="mb-4">
        <label
          class="block text-xs font-semibold text-brand-muted uppercase tracking-wide mb-3"
          >Dirección</label
        >
      </div>

      <p
        v-if="attempted && !form.location.neighborhood_id"
        class="text-xs text-red-500 mb-2"
      >
        Ingresa una dirección para continuar
      </p>
      <div class="flex gap-3 items-center">
        <!-- Búsqueda: 3/4 -->
        <div class="w-3/4">
          <div ref="autocompleteContainer" class="w-full" />
        </div>

        <!-- Barrio detectado: 1/4 -->
        <div class="w-1/4">
          <div
            v-if="neighborhood"
            class="flex items-center gap-3 px-3 py-2.5 rounded-2xl bg-brand-primary-light border border-brand-primary/20"
          >
            <div
              class="w-8 h-8 rounded-full bg-brand-primary flex items-center justify-center shrink-0"
            >
              <MapPin class="w-4 h-4 text-white" />
            </div>
            <div>
              <p
                class="text-xs font-semibold text-brand-muted uppercase tracking-wide"
              >
                Barrio
              </p>
              <p class="text-sm font-bold text-brand-text">
                {{ neighborhood }} <span class="text-brand-primary">✓</span>
              </p>
            </div>
          </div>
          <div
            v-else
            class="flex items-center justify-center border-2 border-dashed border-brand-divider rounded-2xl px-3 py-2.5"
          >
            <p class="text-xs text-brand-muted text-center">
              Barrio detectado automáticamente
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom: NearbyPlaces full width -->
    <div>
      <NearbyPlaces
        v-if="localSelectedPlace"
        :lat="localSelectedPlace.latitude"
        :lon="localSelectedPlace.longitude"
        :property-id="previewId"
      />
      <div
        v-else
        class="h-64 bg-brand-bg rounded-2xl border-2 border-dashed border-brand-divider flex flex-col items-center justify-center gap-3 px-8 text-center"
      >
        <div class="flex gap-4 text-brand-muted/30">
          <MapPin class="w-8 h-8" />
          <Navigation class="w-8 h-8" />
          <Coffee class="w-8 h-8" />
        </div>
        <p class="text-sm font-semibold text-brand-text">
          Descubre qué hay cerca de tu propiedad
        </p>
        <p class="text-xs text-brand-muted">
          Al ingresar la dirección verás un mapa con colegios, hospitales,
          restaurantes, transporte y más — todo lo que le importa a un comprador
          o arrendatario.
        </p>
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

const props = defineProps<{
  form: CreatePropertyForm;
  neighborhoodName?: string | null;
  selectedPlace?: SelectedPlace | null;
  attempted?: boolean;
}>();

const emit = defineEmits<{
  (e: "update:form", v: CreatePropertyForm): void;
  (e: "update:neighborhoodName", v: string | null): void;
  (e: "update:selectedPlace", v: SelectedPlace | null): void;
}>();

const autocompleteContainer = ref<HTMLDivElement | null>(null);
const localSelectedPlace = ref<SelectedPlace | null>(
  props.selectedPlace ?? null
);
const neighborhood = ref<string | null>(props.neighborhoodName ?? null);
const previewId = crypto.randomUUID();

onMounted(async () => {
  await nextTick();
  const { PlaceAutocompleteElement } = await google.maps.importLibrary(
    "places"
  );
  const el = new PlaceAutocompleteElement({});
  autocompleteContainer.value?.appendChild(el);

  el.addEventListener("gmp-select", async (e: any) => {
    const p = e.placePrediction.toPlace();
    await p.fetchFields({
      fields: ["displayName", "formattedAddress", "location"],
    });

    const lat = p.location?.lat();
    const lon = p.location?.lng();

    const place: SelectedPlace = {
      latitude: lat,
      longitude: lon,
      address: p.formattedAddress ?? "",
    };
    localSelectedPlace.value = place;
    emit("update:selectedPlace", place);

    const resolved = await getNeighborhood(lat, lon);
    neighborhood.value = resolved?.name ?? null;
    emit("update:neighborhoodName", neighborhood.value);

    emit("update:form", {
      ...props.form,
      location: {
        latitude: lat,
        longitude: lon,
        neighborhood_id: resolved?.neighborhood_id ?? "",
        city_id: resolved?.city_id ?? "",
        country_id: resolved?.country_id ?? "",
      },
    });
  });
});
</script>
