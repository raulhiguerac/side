import { ref, shallowRef, computed, type Component } from "vue";
import { useUserStore } from "@/stores/user";
import router from "@/router";

import IntentSelector from "@/components/IntentSelector.vue";

const STEP_MAP: Record<string, Component> = {
  city: IntentSelector,
  neighborhood: IntentSelector,
};

export function useOnboarding() {
  const userStore = useUserStore();
  const isModalOpen = ref(false);
  const activeComponent = shallowRef<Component | null>(null);

  const startFlow = async () => {
    if (
      sessionStorage.getItem("onboarding_dismissed") === "true" ||
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

  return { isModalOpen, activeComponent, startFlow, closeFlow };
}
