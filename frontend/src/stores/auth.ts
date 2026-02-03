/**
 * 🏪 AUTH STORE - La "memoria" de autenticación de tu app
 */

import { defineStore } from "pinia";
import axios from "axios";
import router from "@/router";
import { useUserStore } from "./user";

// =========================================================
// 📦 TIPOS Y ENUMERACIONES
// =========================================================

interface UserProfile {
  first_name: string;
  last_name: string;
  phone: string;
  photo_url?: string;
  description?: string;
  intent?: "buyer" | "seller" | "renter" | "explorer";
  account_type: "person" | "organization";
}

interface User extends UserProfile {
  id?: string;
  email?: string;
}

interface ProfileResponse {
  profile: UserProfile;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _authChecked: boolean;
}

// =========================================================
// 🏪 STORE DEFINITION
// =========================================================

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    _authChecked: false,
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
          "http://localhost:8000/v1/users/me/profile",
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

    async login(email: string, password: string): Promise<boolean> {
      try {
        await axios.post(
          "http://localhost:8000/v1/auth/login",
          { email, password },
          { withCredentials: true }
        );

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
        await axios.post("http://localhost:8000/v1/auth/register", userData, {
          withCredentials: true,
        });

        await this.checkAuth(true);
        return this.isAuthenticated;
      } catch (error) {
        return false;
      }
    },

    /**
     * 🚪 LOGOUT OPTIMIZADO
     * Prevenimos el bloqueo de la transición out-in.
     */
    async logout(): Promise<void> {
      try {
        await axios.post(
          "http://localhost:8000/v1/auth/logout",
          {},
          { withCredentials: true }
        );
      } catch (error) {
        console.error("Error en logout:", error);
      } finally {
        // 1. Reseteamos el store de usuario (onboarding) primero
        const userStore = useUserStore();
        userStore.logoutReset();

        // 2. Limpiamos datos locales
        this.user = null;
        this.isAuthenticated = false;

        /**
         * 💡 EL TRUCO: Marcamos _authChecked como true.
         * Esto evita que el router.beforeEach intente llamar a checkAuth()
         * otra vez mientras la animación de salida está ocurriendo.
         */
        this._authChecked = true;

        // 3. Redirigimos al Home o Login
        router.push("/");
      }
    },

    updateUser(userData: Partial<User>): void {
      if (this.user) {
        this.user = { ...this.user, ...userData };
      }
    },
  },
});
