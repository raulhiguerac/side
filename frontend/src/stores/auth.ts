import { defineStore } from "pinia";
import router from "@/router";
import * as usersApi from "@/api/users";
import { useUserStore } from "./user";
import type { AuthState, AuthUser, RegisterPayload } from "@/types/users/auth";
import type { OnboardingStep } from "@/types/users/base";
import { logger } from "@/utils/logger";

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    _authChecked: false,
    onboardingStep: "intent",
    isAdmin: false,
    accountId: null,
  }),

  getters: {
    fullName(): string {
      // Usamos optional chaining para evitar errores en el logout
      if (!this.user) return "";
      return `${this.user?.first_name} ${this.user?.last_name}`;
    },

    isOrganization(): boolean {
      return this.user?.account_type === "organization";
    },

    userAvatar(): string {
      if (this.user?.photo_url) return this.user.photo_url;
      const name = this.fullName || "User";
      return `https://ui-avatars.com/api/?name=${encodeURIComponent(
        name
      )}&background=22C55E&color=fff`;
    },
  },

  actions: {
    async checkAuth(force = false): Promise<void> {
      if (this._authChecked && !force) return;
      if (this.isLoading && this._authChecked) return;

      this.isLoading = true;

      try {
        const { profile } = await usersApi.getAuthProfile();

        this.user = profile;
        this.isAuthenticated = true;
      } catch (error) {
        this.user = null;
        this.isAuthenticated = false;
      } finally {
        this.isLoading = false;
        this._authChecked = true;
      }
    },

    async fillUserData() {
      const data = await usersApi.getAccount();

      this.onboardingStep = data.onboarding_step ?? "intent";
      this.isAdmin = data.is_admin;
      this.accountId = data.account_id;
    },

    async login(email: string, password: string): Promise<boolean> {
      try {
        await usersApi.login({ email, password });

        await this.checkAuth(true);
        return this.isAuthenticated;
      } catch (error) {
        this.user = null;
        this.isAuthenticated = false;
        return false;
      }
    },

    async register(userData: RegisterPayload): Promise<boolean> {
      try {
        await usersApi.register(userData);

        await this.checkAuth(true);
        return this.isAuthenticated;
      } catch (error) {
        return false;
      }
    },

    /** Logout optimizado: no bloquea la transición out-in. */
    async logout(): Promise<void> {
      try {
        await usersApi.logout();
      } catch (error) {
        logger.error("Error en logout:", error);
      } finally {
        // Limpiamos datos locales
        useUserStore().resetInterests();
        this.user = null;
        this.isAuthenticated = false;
        this.onboardingStep = "intent";
        this.isAdmin = false;
        this.accountId = null;

        /** `_authChecked` en true evita que el guard llame a `checkAuth()` durante la animación de salida. */
        this._authChecked = true;

        // Redirigimos al Home o Login
        router.push("/");
      }
    },

    setOnboardingStep(step: OnboardingStep): void {
      this.onboardingStep = step;
    },

    updateUser(userData: Partial<AuthUser>): void {
      if (this.user) {
        this.user = { ...this.user, ...userData };
      }
    },
  },
});
