/**
 * Gestión del Onboarding y Datos de Usuario
 * * Este store se encarga de:
 * 1. Rastrear en qué paso del onboarding está el usuario.
 * 2. Recordar si el usuario cerró el modal manualmente (SessionStorage).
 * 3. Evitar llamadas innecesarias al servidor si ya tenemos los datos.
 */

import { defineStore } from "pinia";
import axios from "axios";
import { API, STORAGE_KEYS } from "@/config";
import { useAuthStore } from "./auth";

interface User {
  account_id: string;
  email: string;
  account_type: string;
  onboarding_step: string;
  is_active: boolean;
}

interface OnboardingState {
  onboardingStep: string;
  hasCheckedOnboarding: boolean;
  userDismissedModal: boolean;
}

interface UserLocation {
  country_name: string;
  latitude: number;
  longitude: number;
}

export const useUserStore = defineStore("user", {
  state: (): OnboardingState => ({
    onboardingStep: "intent",
    hasCheckedOnboarding: false,
    userDismissedModal:
      sessionStorage.getItem(STORAGE_KEYS.ONBOARDING_DISMISSED) === "true",
  }),

  actions: {
    async checkOnboardingStep(): Promise<string> {
      const authStore = useAuthStore();
      if (!authStore.isAuthenticated) throw new Error("AUTH_REQUIRED");
      if (this.userDismissedModal) return "done";
      if (this.hasCheckedOnboarding) return this.onboardingStep;

      try {
        const { data } = await axios.get<User>(
          `${API.USERS_BASE_URL}/v1/users/me/`,
          { withCredentials: true }
        );

        this.onboardingStep = data.onboarding_step ?? "intent";
        this.hasCheckedOnboarding = true;

        return this.onboardingStep;
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 401)
          authStore.logout();
        throw error;
      }
    },

    async detectLocation(): Promise<UserLocation> {
      const raw = localStorage.getItem(STORAGE_KEYS.USER_LOCATION);
      if (raw) return JSON.parse(raw) as UserLocation;
      const { data } = await axios.get(API.IPAPI_URL);
      const location: UserLocation = data;
      localStorage.setItem(
        STORAGE_KEYS.USER_LOCATION,
        JSON.stringify(location)
      );
      return location;
    },

    dismissModal() {
      this.userDismissedModal = true;
      sessionStorage.setItem(STORAGE_KEYS.ONBOARDING_DISMISSED, "true");
      this.onboardingStep = "done";
    },

    logoutReset() {
      this.userDismissedModal = false;
      this.hasCheckedOnboarding = false;
      this.onboardingStep = "done";
      sessionStorage.removeItem(STORAGE_KEYS.ONBOARDING_DISMISSED);
      console.log("✨ Onboarding reseteado para nueva sesión.");
    },
  },
});
