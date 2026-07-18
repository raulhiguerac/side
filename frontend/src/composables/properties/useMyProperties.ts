import { ref } from "vue";
import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";
import type { PropertyCard } from "@/types/feed";

export function useMyProperties() {
  const properties = ref<PropertyCard[]>([]);
  const isLoading = ref(true);

  async function fetchProperties() {
    isLoading.value = true;
    try {
      const { data } = await propertiesApi.get<PropertyCard[]>(
        PROPERTIES_ENDPOINTS.me
      );
      properties.value = data;
    } catch (error) {
      console.error("Error al cargar propiedades:", error);
      properties.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  return { properties, isLoading, fetchProperties };
}
