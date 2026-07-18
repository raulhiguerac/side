import propertiesApi from "@/api/propertiesApi";
import { PROPERTIES_ENDPOINTS } from "@/constants/propertiesEndpoints";

export function usePropertyVisibility() {
  async function toggleVisibility(propertyId: string): Promise<boolean> {
    try {
      await propertiesApi.post(PROPERTIES_ENDPOINTS.visibility(propertyId));
      return true;
    } catch (error) {
      console.error("Error al cambiar visibilidad:", error);
      return false;
    }
  }

  return { toggleVisibility };
}
