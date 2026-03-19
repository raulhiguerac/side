import { ref, shallowRef, type Component } from "vue";
import axios from "axios";

import { API, STORAGE_KEYS } from "@/config";
import { useUserStore } from "@/stores/user";
import IntentSelector from "@/components/onboarding/IntentSelector.vue";
import LocalitySelector from "@/components/onboarding/LocalitySelector.vue";
import NeighborhoodSelector from "@/components/onboarding/NeighborhoodSelector.vue";

const STEP_MAP: Record<string, Component> = {
  intent: IntentSelector,
  city: LocalitySelector,
  neighborhood: NeighborhoodSelector,
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

  const saveCity = async (ids: string[]) => {
    try {
      await axios.post(
        `${API.USERS_BASE_URL}/v1/onboarding/city`,
        { locality_ids: ids },
        { withCredentials: true }
      );
      userStore.onboardingStep = "neighborhood";
      activeComponent.value = STEP_MAP["neighborhood"];
    } catch (e) {
      console.error("Onboarding saveCity error", e);
    }
  };

  return { isModalOpen, activeComponent, startFlow, closeFlow, saveCity };
}
