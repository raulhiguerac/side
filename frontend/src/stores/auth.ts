import { defineStore } from "pinia";
import axios from "axios";
import router from "@/router";
import { API } from "@/config";
import usersApi from "@/api/usersApi";
import { useUserStore } from "./user";
import type { AuthProfile, AuthUser, User as AccountUser } from "@/types/user";

interface ProfileResponse {
  profile: AuthProfile;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _authChecked: boolean;
  onboardingStep: string;
  isAdmin: boolean;
  accountId: string | null;
}

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
        const response = await axios.get<ProfileResponse>(
          `${API.USERS_BASE_URL}/v1/users/me/profile`,
          { withCredentials: true }
        );

        this.user = response.data.profile;
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
      const { data } = await usersApi.get<AccountUser>("/v1/users/me/");

      this.onboardingStep = data.onboarding_step ?? "intent";
      this.isAdmin = data.is_admin;
      this.accountId = data.account_id;
    },

    async login(email: string, password: string): Promise<boolean> {
      try {
        await usersApi.post("/v1/auth/login", { email, password });

        await this.checkAuth(true);
        return this.isAuthenticated;
      } catch (error) {
        this.user = null;
        this.isAuthenticated = false;
        return false;
      }
    },

    async register(userData: any): Promise<boolean> {
      try {
        await usersApi.post("/v1/auth/register", userData);

        await this.checkAuth(true);
        return this.isAuthenticated;
      } catch (error) {
        return false;
      }
    },

    /** Logout optimizado: no bloquea la transición out-in. */
    async logout(): Promise<void> {
      try {
        await axios.post(
          `${API.USERS_BASE_URL}/v1/auth/logout`,
          {},
          { withCredentials: true }
        );
      } catch (error) {
        console.error("Error en logout:", error);
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

    updateUser(userData: Partial<AuthUser>): void {
      if (this.user) {
        this.user = { ...this.user, ...userData };
      }
    },
  },
});
