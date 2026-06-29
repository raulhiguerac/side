import { ref, shallowRef, type Component } from "vue";
import { STORAGE_KEYS } from "@/config";
import usersApi from "@/api/usersApi";
import { useUserStore } from "@/stores/user";
import IntentSelector from "@/components/onboarding/IntentSelector.vue";
import LocalitySelector from "@/components/onboarding/LocalitySelector.vue";
import NeighborhoodSelector from "@/components/onboarding/NeighborhoodSelector.vue";
import PropertyTypeSelector from "@/components/onboarding/PropertyTypeSelector.vue";

const STEP_MAP: Record<string, Component> = {
  intent: IntentSelector,
  city: LocalitySelector,
  neighborhood: NeighborhoodSelector,
  property_type: PropertyTypeSelector,
};

const isModalOpen = ref(false);
const activeComponent = shallowRef<Component | null>(null);

export function useOnboarding() {
  const userStore = useUserStore();

  const startFlow = async () => {
    if (
      sessionStorage.getItem(STORAGE_KEYS.ONBOARDING_DISMISSED) === "true" ||
      userStore.userDismissedModal
    ) {
      return;
    }

    try {
      const step = await userStore.checkOnboardingStep();

      if (step != "done" && STEP_MAP[step]) {
        activeComponent.value = STEP_MAP[step];
        isModalOpen.value = true;
      }
    } catch (e) {
      console.error("Onboarding error", e);
    }
  };

  const closeFlow = () => {
    isModalOpen.value = false;
    userStore.dismissModal();
  };

  const advanceToCity = () => {
    userStore.onboardingStep = "city";
    activeComponent.value = STEP_MAP["city"];
  };

  const saveCity = async (localities: { id: string; name: string }[]) => {
    try {
      await usersApi.post("/v1/onboarding/city", {
        locality_ids: localities.map((l) => l.id),
      });
      userStore.userInterests.localities = localities.map((l) => l.id);
      userStore.onboardingStep = "neighborhood";
      activeComponent.value = STEP_MAP["neighborhood"];
    } catch (e) {
      console.error("Onboarding saveCity error", e);
    }
  };

  const saveNeighborhoods = async (
    localities: { locality_id: string; neighborhoods: Record<number, string> }[]
  ) => {
    try {
      await usersApi.post("/v1/onboarding/neighborhood", { localities });
      userStore.onboardingStep = "property_type";
      activeComponent.value = STEP_MAP["property_type"];
    } catch (e) {
      console.error("Onboarding saveNeighborhoods error", e);
    }
  };

  const savePropertyTypes = async (selections: Record<string, string[]>) => {
    try {
      await Promise.all(
        Object.entries(selections).map(([locality_id, property_type]) =>
          usersApi.post("/v1/onboarding/property-type", {
            locality_id,
            property_type,
          })
        )
      );
      closeFlow();
    } catch (e) {
      console.error("Onboarding savePropertyTypes error", e);
    }
  };

  return {
    isModalOpen,
    activeComponent,
    startFlow,
    closeFlow,
    advanceToCity,
    saveCity,
    saveNeighborhoods,
    savePropertyTypes,
  };
}
