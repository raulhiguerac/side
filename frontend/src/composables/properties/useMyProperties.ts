import { ref } from "vue";
import * as propertiesApi from "@/api/properties";
import type { PropertyCard } from "@/types/feed/cards";
import { logger } from "@/utils/logger";

export function useMyProperties() {
  const properties = ref<PropertyCard[]>([]);
  const isLoading = ref(true);

  async function fetchProperties() {
    isLoading.value = true;
    try {
      properties.value = await propertiesApi.getMyProperties();
    } catch (error) {
      logger.error("Error al cargar propiedades:", error);
      properties.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  return { properties, isLoading, fetchProperties };
}
