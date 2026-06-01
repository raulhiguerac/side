import { ref, reactive, computed, watch, nextTick, type Ref } from "vue";
declare const google: any;

export interface AvmFormPayload {
  property_type: "apartment" | "house";
  area_m2: number;
  bedrooms: number;
  bathrooms: number;
  parking_spots: number;
  stratum: number;
  year_built: number | null;
}

export interface AvmPredictRequest extends AvmFormPayload {
  lat: number;
  lon: number;
  barrio_ideca: string;
}

interface AvmFormState {
  property_type: "apartment" | "house";
  area_m2: number | null;
  bedrooms: number;
  bathrooms: number;
  parking_spots: number;
  stratum: number;
  year_built: number | null;
}

export interface SelectedPlace {
  latitude: number;
  longitude: number;
  address: string;
}

export function useAvmForm(autocompleteContainer: Ref<HTMLDivElement | null>) {
  const step = ref(1);
  const place = ref<SelectedPlace | null>(null);
  const form = reactive<AvmFormState>({
    property_type: "apartment",
    area_m2: null,
    bedrooms: 3,
    bathrooms: 2,
    parking_spots: 1,
    stratum: 3,
    year_built: null,
  });
  const stepLabels = ["Tipo", "Detalles", "Ubicación"];
  const stepperFields = [
    {
      key: "bedrooms" as const,
      label: "Habitaciones",
      inc: 1,
      min: 0,
      max: 20,
    },
    { key: "bathrooms" as const, label: "Baños", inc: 0.5, min: 0, max: 20 },
    {
      key: "parking_spots" as const,
      label: "Parqueaderos",
      inc: 1,
      min: 0,
      max: 10,
    },
  ];

  watch(step, async (val) => {
    if (val !== 3) return;
    await nextTick();
    await new Promise((r) => setTimeout(r, 260));
    if (autocompleteContainer.value?.childElementCount) return;
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
      place.value = {
        latitude: p.location?.lat(),
        longitude: p.location?.lng(),
        address: p.formattedAddress ?? "",
      };
    });
  });

  const canAdvance = computed(() => {
    if (step.value === 2) return !!form.area_m2 && form.area_m2 > 0;
    if (step.value === 3) return !!place.value;
    return true;
  });

  function nextStep() {
    if (canAdvance.value) step.value++;
  }

  type StepperKey = "bedrooms" | "bathrooms" | "parking_spots";

  function increment(key: StepperKey, inc: number, max: number) {
    if (form[key] < max) form[key] = Math.round((form[key] + inc) * 10) / 10;
  }

  function decrement(key: StepperKey, inc: number, min: number) {
    if (form[key] > min) form[key] = Math.round((form[key] - inc) * 10) / 10;
  }

  function toPayload(): AvmFormPayload | null {
    if (form.area_m2 == null) return null;
    return {
      property_type: form.property_type,
      area_m2: form.area_m2,
      bedrooms: form.bedrooms,
      bathrooms: form.bathrooms,
      parking_spots: form.parking_spots,
      stratum: form.stratum,
      year_built: form.year_built,
    };
  }

  return {
    step,
    form,
    stepLabels,
    stepperFields,
    place,
    canAdvance,
    nextStep,
    increment,
    decrement,
    toPayload,
  };
}
