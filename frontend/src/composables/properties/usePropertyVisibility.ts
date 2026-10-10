import * as propertiesApi from "@/api/properties";
import { logger } from "@/utils/logger";

export function usePropertyVisibility() {
  async function toggleVisibility(propertyId: string): Promise<boolean> {
    try {
      await propertiesApi.toggleVisibility(propertyId);
      return true;
    } catch (error) {
      logger.error("Error al cambiar visibilidad:", error);
      return false;
    }
  }

  return { toggleVisibility };
}
