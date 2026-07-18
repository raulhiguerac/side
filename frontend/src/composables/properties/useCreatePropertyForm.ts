import { ref } from "vue";
import axios from "axios";
import type { CreatePropertyForm } from "@/types/properties";
import type { SelectedPlace } from "@/composables/avm/useAvmForm";
import propertiesApi from "@/api/propertiesApi";

export function useCreatePropertyForm() {
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);
  const errorCode = ref<string | null>(null);
  const attempted = ref(false);
  const neighborhoodName = ref<string | null>(null);
  const selectedPlace = ref<SelectedPlace | null>(null);

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

  async function createListing(form: CreatePropertyForm) {
    try {
      loading.value = true;
      error.value = null;
      errorCode.value = null;
      const { data } = await propertiesApi.post<string>(
        "/v1/properties/create",
        form
      );
      return data;
    } catch (e) {
      error.value = "No se pudo crear la propiedad";
      if (axios.isAxiosError(e)) {
        errorCode.value = `PUB-${e.response?.status ?? "000"}`;
      }
      throw e;
    } finally {
      loading.value = false;
    }
  }

  return {
    form,
    loading,
    error,
    errorCode,
    attempted,
    neighborhoodName,
    selectedPlace,
    createListing,
  };
}
