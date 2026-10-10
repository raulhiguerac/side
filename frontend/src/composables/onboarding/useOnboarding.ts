import * as usersApi from "@/api/users";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import type { CatalogItem } from "@/types/catalog/base";
import type { NeighborhoodSelection } from "@/types/users/interests";
import { logger } from "@/utils/logger";

// Guarda cada paso y avanza el flujo; abrir y cerrar el modal es del padre.
export function useOnboarding() {
  const authStore = useAuthStore();
  const userStore = useUserStore();

  function shouldStart(): boolean {
    return (
      !userStore.isOnboardingDismissed() && authStore.onboardingStep !== "done"
    );
  }

  function completeIntent() {
    authStore.setOnboardingStep("city");
  }

  async function saveCity(localities: CatalogItem[]): Promise<boolean> {
    try {
      const ids = localities.map((l) => l.id);
      await usersApi.saveCities(ids);
      userStore.setLocalities(ids);
      authStore.setOnboardingStep("neighborhood");
      return true;
    } catch (e) {
      logger.error("Onboarding saveCity error", e);
      return false;
    }
  }

  async function saveNeighborhoods(
    localities: NeighborhoodSelection[]
  ): Promise<boolean> {
    try {
      await usersApi.saveNeighborhoods(localities);
      authStore.setOnboardingStep("property_type");
      return true;
    } catch (e) {
      logger.error("Onboarding saveNeighborhoods error", e);
      return false;
    }
  }

  async function savePropertyTypes(
    selections: Record<string, string[]>
  ): Promise<boolean> {
    try {
      await Promise.all(
        Object.entries(selections).map(([localityId, types]) =>
          usersApi.savePropertyTypes(localityId, types)
        )
      );
      return true;
    } catch (e) {
      logger.error("Onboarding savePropertyTypes error", e);
      return false;
    }
  }

  return {
    shouldStart,
    completeIntent,
    saveCity,
    saveNeighborhoods,
    savePropertyTypes,
  };
}
