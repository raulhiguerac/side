/** Onboarding: paso actual, si se cerró el modal (sessionStorage) y cache de los datos del usuario. */

import { defineStore } from "pinia";
import axios from "axios";
import { API, STORAGE_KEYS } from "@/config";
import usersApi from "@/api/usersApi";
import { useAuthStore } from "./auth";
import type { UserLocation, UserInterests, UserState } from "@/types/user";

export const useUserStore = defineStore("user", {
  state: (): UserState => ({
    userInterests: { localities: [], neighborhoods: {}, properties: {} },
  }),

  actions: {
    async checkInterests(): Promise<UserInterests> {
      if (this.userInterests.localities.length > 0) return this.userInterests;
      const { data } = await usersApi.get<UserInterests>(
        "/v1/users/me/interests"
      );

      this.userInterests = data;
      return data;
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

    resetInterests() {
      this.userInterests = {
        localities: [],
        neighborhoods: {},
        properties: {},
      };
    },

    isOnboardingDismissed(): boolean {
      const authStore = useAuthStore();
      if (!authStore.accountId) return false;
      return (
        sessionStorage.getItem(
          STORAGE_KEYS.ONBOARDING_DISMISSED(authStore.accountId)
        ) === "true"
      );
    },

    dismissModal() {
      const authStore = useAuthStore();
      if (!authStore.accountId) return;
      sessionStorage.setItem(
        STORAGE_KEYS.ONBOARDING_DISMISSED(authStore.accountId),
        "true"
      );
    },
  },
});
