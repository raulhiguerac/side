/**
 * Gestión del Onboarding y Datos de Usuario
 * * Este store se encarga de:
 * 1. Rastrear en qué paso del onboarding está el usuario.
 * 2. Recordar si el usuario cerró el modal manualmente (SessionStorage).
 * 3. Evitar llamadas innecesarias al servidor si ya tenemos los datos.
 */

import { defineStore } from "pinia";
import axios from "axios";
import { useAuthStore } from "./auth";

interface User {
  account_id: string;
  email: string;
  account_type: string;
  onboarding_step: number;
  is_active: boolean;
}

interface OnboardingState {
  onboardingStep: number;
  hasCheckedOnboarding: boolean;
  userDismissedModal: boolean;
}

export const useUserStore = defineStore("user", {
  state: (): OnboardingState => ({
    onboardingStep: 0,
    hasCheckedOnboarding: false,
    userDismissedModal:
      sessionStorage.getItem("onboarding_dismissed") === "true",
  }),

  actions: {
    async checkOnboardingStep(): Promise<number> {
      const authStore = useAuthStore();

      if (!authStore.isAuthenticated) throw new Error("AUTH_REQUIRED");

      if (this.userDismissedModal) return 0;

      if (this.hasCheckedOnboarding) return this.onboardingStep;

      try {
        const { data } = await axios.get<User>(
          "http://localhost:8000/v1/users/me/",
          { withCredentials: true }
        );

        this.onboardingStep = data.onboarding_step ?? 1;
        this.hasCheckedOnboarding = true;

        return this.onboardingStep;
      } catch (error: any) {
        if (error.response?.status === 401) authStore.logout();
        throw error;
      }
    },

    dismissModal() {
      this.userDismissedModal = true;
      sessionStorage.setItem("onboarding_dismissed", "true");
      this.onboardingStep = 0;
    },

    logoutReset() {
      this.userDismissedModal = false;
      this.hasCheckedOnboarding = false;
      this.onboardingStep = 0;
      sessionStorage.removeItem("onboarding_dismissed");
      console.log("✨ Onboarding reseteado para nueva sesión.");
    },
  },
});
